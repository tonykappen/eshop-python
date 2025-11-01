"""Async CLEF log dispatcher for Seq and NDJSON file output."""

import asyncio
import contextlib
import json
from asyncio import Queue
from datetime import date
from pathlib import Path
from typing import Any

try:
    import httpx

    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False


def _resolve_log_directory(log_directory: str) -> Path:
    """Resolve log directory path relative to backend directory.

    Args:
        log_directory: Relative or absolute log directory path

    Returns:
        Resolved absolute Path to log directory
    """
    log_path = Path(log_directory)

    # If already absolute, return as is
    if log_path.is_absolute():
        return log_path

    # Get the backend directory (parent of app directory)
    # __file__ is in backend/app/core/logging/clef_dispatcher.py
    # So we go: clef_dispatcher.py -> logging/ -> core/ -> app/ -> backend/
    backend_dir = Path(__file__).parent.parent.parent.parent

    # Resolve relative to backend directory
    resolved_path = backend_dir / log_path

    return resolved_path


class CLEFLogDispatcher:
    """Async log dispatcher that sends CLEF events to Seq and NDJSON files."""

    def __init__(
        self,
        seq_url: str | None = None,
        seq_api_key: str | None = None,
        log_directory: str = "run_time/logs",
        queue_max_size: int = 10000,
        batch_size: int = 50,
        flush_interval: float = 1.0,
    ):
        """Initialize the dispatcher."""
        self.seq_url = seq_url.rstrip("/") if seq_url else None
        self.seq_api_key = seq_api_key
        # Resolve log directory relative to backend directory
        self.log_directory = _resolve_log_directory(log_directory)
        self.queue: Queue[dict[str, Any]] = Queue(maxsize=queue_max_size)
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self._running = False
        self._task: asyncio.Task | None = None
        self._client: httpx.AsyncClient | None = None
        self._current_date = date.today()
        self._file_handles: dict[str, Any] = {}  # Track open file handles

        # Create log directory
        self.log_directory.mkdir(exist_ok=True, parents=True)

        # Initialize rotation check (handle files from previous days)
        self._rotate_ndjson_files_on_init()

        # Track stats
        self.stats = {
            "enqueued": 0,
            "sent_to_seq": 0,
            "sent_to_file": 0,
            "seq_errors": 0,
            "file_errors": 0,
            "dropped": 0,
        }

    async def start(self) -> None:
        """Start the async dispatcher."""
        if self._running:
            return

        self._running = True

        # Create async HTTP client for Seq
        if HTTPX_AVAILABLE and self.seq_url:
            self._client = httpx.AsyncClient(
                timeout=5.0,
                limits=httpx.Limits(max_connections=10, max_keepalive_connections=5),
            )

        # Start background task
        self._task = asyncio.create_task(self._process_queue())

    async def stop(self) -> None:
        """Stop the dispatcher and flush remaining logs."""
        self._running = False

        if self._task:
            await self._task

        # Flush any remaining logs
        await self._flush_remaining()

        # Close HTTP client
        if self._client:
            await self._client.aclose()

    async def enqueue(self, event: dict[str, Any]) -> None:
        """Enqueue a CLEF event for async processing."""
        try:
            # Non-blocking put with immediate drop if queue is full
            self.queue.put_nowait(event)
            self.stats["enqueued"] += 1
        except asyncio.QueueFull:
            # Drop oldest or sample
            self.stats["dropped"] += 1
            # Try to mark as sampled
            event["sampled"] = True
            # Try one more time
            with contextlib.suppress(asyncio.QueueFull):
                self.queue.put_nowait(event)

    async def _process_queue(self) -> None:
        """Background task that processes queued log events."""
        batch: list[dict[str, Any]] = []
        last_flush = asyncio.get_event_loop().time()

        while self._running or not self.queue.empty():
            try:
                # Wait for event with timeout
                try:
                    event = await asyncio.wait_for(
                        self.queue.get(), timeout=self.flush_interval
                    )
                    batch.append(event)
                except TimeoutError:
                    pass  # Flush on timeout

                current_time = asyncio.get_event_loop().time()
                should_flush = (
                    len(batch) >= self.batch_size
                    or (current_time - last_flush) >= self.flush_interval
                )

                if should_flush and batch:
                    await self._flush_batch(batch)
                    batch = []
                    last_flush = current_time

            except Exception as e:
                # Log error to stderr to avoid log loops
                print(f"Error in log dispatcher: {e}", flush=True)
                await asyncio.sleep(0.1)

        # Final flush
        if batch:
            await self._flush_batch(batch)

    async def _flush_batch(self, batch: list[dict[str, Any]]) -> None:
        """Flush a batch of events to Seq and NDJSON files."""
        if not batch:
            return

        # Send to Seq (async)
        if self._client and self.seq_url:
            asyncio.create_task(self._send_to_seq_batch(batch))

        # Write to NDJSON files (async)
        asyncio.create_task(self._write_to_ndjson_batch(batch))

    async def _send_to_seq_batch(self, batch: list[dict[str, Any]]) -> None:
        """Send a batch of events to Seq with retry."""
        if not self._client or not self.seq_url:
            return

        try:
            headers = {"Content-Type": "application/vnd.serilog.clef"}
            if self.seq_api_key:
                headers["X-Seq-ApiKey"] = self.seq_api_key

            # Seq CLEF ingestion expects newline-delimited JSON
            payload = "\n".join(json.dumps(event, default=str) for event in batch)

            response = await self._client.post(
                f"{self.seq_url}/api/events/raw",
                content=payload,
                headers=headers,
            )
            response.raise_for_status()
            self.stats["sent_to_seq"] += len(batch)

        except Exception as e:
            self.stats["seq_errors"] += len(batch)
            # Fallback: write to file if Seq fails
            await self._write_to_ndjson_batch(batch, _fallback=True)
            # Log error to stderr
            print(f"Failed to send logs to Seq: {e}", flush=True)

    async def _write_to_ndjson_batch(
        self, batch: list[dict[str, Any]], _fallback: bool = False
    ) -> None:
        """Write batch to NDJSON files."""
        try:
            # Group events by type
            access_events = []
            app_events = []

            for event in batch:
                event_name = event.get("@m", "")
                if event_name in ("begin_request", "response_sent"):
                    access_events.append(event)
                else:
                    app_events.append(event)

            # Write access logs
            if access_events:
                await self._append_to_file("access.ndjson", access_events)

            # Write app logs
            if app_events:
                await self._append_to_file("app.ndjson", app_events)

            self.stats["sent_to_file"] += len(batch)

        except Exception as e:
            self.stats["file_errors"] += len(batch)
            print(f"Failed to write logs to file: {e}", flush=True)

    def _get_dated_filename(self, base_filename: str) -> str:
        """Get the appropriate filename based on current date.

        Today's logs use base_filename (e.g., app.ndjson).
        Previous days use base_filename_YYYY-MM-DD (e.g., app_2024-01-15.ndjson).
        """
        current_date = date.today()

        # If date changed, rotate old files
        if current_date != self._current_date:
            self._rotate_ndjson_files()
            self._current_date = current_date

        # Always return base filename for today (rotation happens at day boundary)
        return base_filename

    def _rotate_ndjson_files_on_init(self) -> None:
        """Check and rotate NDJSON files on initialization if they're from a previous day."""
        current_date = date.today()
        base_files = ["app.ndjson", "access.ndjson"]

        for base_file in base_files:
            file_path = self.log_directory / base_file
            if file_path.exists():
                # Check file modification time to see if it's from today
                file_mtime = date.fromtimestamp(file_path.stat().st_mtime)

                # If file is from a previous day, rename it
                if file_mtime < current_date and file_path.stat().st_size > 0:
                    base_name = file_path.stem
                    extension = file_path.suffix
                    dated_filename = (
                        f"{base_name}_{file_mtime.strftime('%Y-%m-%d')}{extension}"
                    )
                    dated_path = self.log_directory / dated_filename

                    try:
                        file_path.rename(dated_path)
                    except Exception as e:
                        print(f"Failed to rotate {base_file} on init: {e}", flush=True)

    def _rotate_ndjson_files(self) -> None:
        """Rotate NDJSON files when date changes."""
        yesterday = self._current_date

        # Files that need rotation
        base_files = ["app.ndjson", "access.ndjson"]

        for base_file in base_files:
            file_path = self.log_directory / base_file

            # If file exists and has content, rename it with date
            if file_path.exists() and file_path.stat().st_size > 0:
                base_name = file_path.stem  # e.g., 'app' from 'app.ndjson'
                extension = file_path.suffix  # e.g., '.ndjson'
                dated_filename = (
                    f"{base_name}_{yesterday.strftime('%Y-%m-%d')}{extension}"
                )
                dated_path = self.log_directory / dated_filename

                # Close any open handle for this file
                if base_file in self._file_handles:
                    try:
                        handle = self._file_handles[base_file]
                        if hasattr(handle, "close"):
                            handle.close()
                    except Exception:
                        pass
                    del self._file_handles[base_file]

                # Rename the file
                try:
                    file_path.rename(dated_path)
                except Exception as e:
                    print(f"Failed to rotate {base_file}: {e}", flush=True)

    async def _append_to_file(
        self, filename: str, events: list[dict[str, Any]]
    ) -> None:
        """Append events to NDJSON file with daily rotation."""
        # Get the correct filename (rotates if needed)
        current_filename = self._get_dated_filename(filename)
        file_path = self.log_directory / current_filename

        # Use aiofiles if available, otherwise sync write in thread pool
        try:
            import aiofiles

            # Open file in append mode
            async with aiofiles.open(file_path, "a") as f:
                for event in events:
                    await f.write(json.dumps(event, default=str) + "\n")
        except ImportError:
            # Fallback to sync write in executor
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None, self._sync_append_to_file, file_path, events
            )

    def _sync_append_to_file(
        self, file_path: Path, events: list[dict[str, Any]]
    ) -> None:
        """Synchronous fallback for file writing."""
        with open(file_path, "a") as f:
            for event in events:
                f.write(json.dumps(event, default=str) + "\n")

    async def _flush_remaining(self) -> None:
        """Flush any remaining events in the queue."""
        batch = []
        while not self.queue.empty():
            try:
                batch.append(self.queue.get_nowait())
                if len(batch) >= self.batch_size:
                    await self._flush_batch(batch)
                    batch = []
            except asyncio.QueueEmpty:
                break

        if batch:
            await self._flush_batch(batch)


# Global dispatcher instance
_dispatcher: CLEFLogDispatcher | None = None


def get_dispatcher() -> CLEFLogDispatcher | None:
    """Get the global dispatcher instance."""
    return _dispatcher


def set_dispatcher(dispatcher: CLEFLogDispatcher) -> None:
    """Set the global dispatcher instance."""
    global _dispatcher
    _dispatcher = dispatcher


async def init_dispatcher(
    seq_url: str | None = None,
    seq_api_key: str | None = None,
    log_directory: str = "run_time/logs",
    queue_max_size: int = 10000,
    batch_size: int = 50,
    flush_interval: float = 1.0,
) -> CLEFLogDispatcher:
    """Initialize and start the global dispatcher."""
    global _dispatcher

    if _dispatcher:
        await _dispatcher.stop()

    _dispatcher = CLEFLogDispatcher(
        seq_url=seq_url,
        seq_api_key=seq_api_key,
        log_directory=log_directory,
        queue_max_size=queue_max_size,
        batch_size=batch_size,
        flush_interval=flush_interval,
    )

    await _dispatcher.start()
    return _dispatcher


async def shutdown_dispatcher() -> None:
    """Shutdown the global dispatcher."""
    global _dispatcher
    if _dispatcher:
        await _dispatcher.stop()
        _dispatcher = None
