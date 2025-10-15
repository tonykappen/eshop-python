#!/usr/bin/env python3
"""Test CLEF logging implementation and validate compliance."""

import asyncio
import json
import sys
from pathlib import Path

# Add the backend directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.config.settings import settings
from app.core.logging.clef_dispatcher import init_dispatcher
from app.core.logging.clef_logger import get_clef_logger
from app.core.logging.logger import configure_logging

# Required fields according to the spec
REQUIRED_FIELDS = {
    "@t",  # UTC timestamp with Z
    "@l",  # level (DEBUG|INFO|WARNING|ERROR|CRITICAL)
    "@m",  # event name
    "service",  # e.g., eshop-api
    "version",  # e.g., 1.3.0+git.abc123
    "env",  # dev|staging|prod
    "logger",
    "module",
    "function",
    "line",
}


async def test_clef_logging():
    """Test CLEF logging and validate format."""
    print("🧪 Testing CLEF Logging Implementation")
    print("=" * 60)

    # Configure logging
    configure_logging(
        log_level=settings.log_level,
        log_format="json",
        enable_seq=settings.log_enable_seq,
        seq_url=settings.seq_url,
        seq_api_key=settings.seq_api_key,
        enable_file_logging=True,
        log_directory=settings.log_directory,
        separate_server_logs=False,
        enable_console=True,
        environment=settings.environment,
    )

    # Initialize dispatcher
    print("\n📊 Initializing dispatcher...")
    print(f"   Seq URL: {settings.seq_url}")
    print(f"   Log Directory: {settings.log_directory}")

    dispatcher = await init_dispatcher(
        seq_url=settings.seq_url,
        seq_api_key=settings.seq_api_key,
        log_directory=settings.log_directory,
        queue_max_size=1000,
        batch_size=10,
        flush_interval=0.5,
    )

    print("✅ Dispatcher initialized\n")

    # Get a CLEF logger
    logger = get_clef_logger("test.clef_logger")

    # Test different log levels
    print("📝 Emitting test logs...")
    logger.info("Test INFO message")
    logger.warning("Test WARNING message")
    logger.debug("Test DEBUG message")

    try:
        # Test error logging with exception
        raise ValueError("Test error for CLEF logging")
    except Exception:
        logger.error("Test ERROR with exception", exc_info=True)

    # Wait for logs to be processed
    print("⏳ Waiting for logs to be processed...")
    await asyncio.sleep(2)

    # Check dispatcher stats
    print("\n📊 Dispatcher Statistics:")
    for key, value in dispatcher.stats.items():
        print(f"   {key}: {value}")

    # Check if log files were created
    log_dir = Path(settings.log_directory)
    print(f"\n📁 Checking log directory: {log_dir}")

    if log_dir.exists():
        print("✅ Log directory exists")

        # List files
        log_files = list(log_dir.glob("*.ndjson"))
        print(f"\n📄 Log files found: {len(log_files)}")
        for log_file in log_files:
            print(f"   - {log_file.name} ({log_file.stat().st_size} bytes)")

            # Validate CLEF format in files
            if log_file.stat().st_size > 0:
                print(f"\n🔍 Validating {log_file.name}...")
                with open(log_file) as f:
                    for i, line in enumerate(f, 1):
                        try:
                            event = json.loads(line.strip())

                            # Check required fields
                            missing_fields = REQUIRED_FIELDS - set(event.keys())
                            if missing_fields:
                                print(
                                    f"   ❌ Line {i}: Missing fields: {missing_fields}"
                                )
                            else:
                                print(f"   ✅ Line {i}: All required fields present")

                            # Validate field formats
                            errors = []

                            # Check @t format (ISO 8601 with Z)
                            if "@t" in event and not event["@t"].endswith("Z"):
                                errors.append("@t must end with Z")

                            # Check @l is valid level
                            if "@l" in event:
                                valid_levels = {
                                    "DEBUG",
                                    "INFO",
                                    "WARNING",
                                    "ERROR",
                                    "CRITICAL",
                                }
                                if event["@l"] not in valid_levels:
                                    errors.append(f"@l must be one of {valid_levels}")

                            if errors:
                                print(f"   ⚠️  Validation errors: {', '.join(errors)}")

                            # Print sample event (first one only)
                            if i == 1:
                                print("\n📋 Sample CLEF Event:")
                                print(json.dumps(event, indent=2))

                        except json.JSONDecodeError as e:
                            print(f"   ❌ Line {i}: Invalid JSON: {e}")
    else:
        print(f"❌ Log directory does not exist: {log_dir}")
        print("   Creating directory...")
        log_dir.mkdir(parents=True, exist_ok=True)

    # Shutdown
    print("\n🛑 Shutting down dispatcher...")
    await dispatcher.stop()
    print("✅ Test completed\n")

    print("=" * 60)
    print("Summary:")
    print(f"  - Logs sent to Seq: {dispatcher.stats['sent_to_seq']}")
    print(f"  - Logs written to files: {dispatcher.stats['sent_to_file']}")
    print(f"  - Seq errors: {dispatcher.stats['seq_errors']}")
    print(f"  - Dropped: {dispatcher.stats['dropped']}")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_clef_logging())
