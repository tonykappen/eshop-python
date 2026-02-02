"""Transactional Outbox pattern for reliable messaging."""

from app.core.messaging.outbox.outbox_dispatcher import (
    IOutboxDispatcher,
    OutboxDispatcher,
)
from app.core.messaging.outbox.outbox_message_orm import (
    OutboxMessage,
    OutboxMessageStatus,
)
from app.core.messaging.outbox.outbox_publisher_worker import OutboxPublisherWorker
from app.core.messaging.outbox.outbox_service import IOutboxService, OutboxService
from app.core.messaging.outbox.worker_factory import create_outbox_worker
from app.core.messaging.outbox.worker_registry import (
    OutboxWorkerRegistry,
    outbox_worker_registry,
)

# Backward compatibility: Re-export from the old outbox.py module
# Since Python 3 prefers packages over modules, we need to explicitly load the .py file
import importlib.util
from pathlib import Path

_parent_dir = Path(__file__).parent.parent
_outbox_module_path = _parent_dir / "outbox.py"
if _outbox_module_path.exists():
    spec = importlib.util.spec_from_file_location(
        "app.core.messaging._outbox_legacy", _outbox_module_path
    )
    if spec and spec.loader:
        _outbox_legacy = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(_outbox_legacy)
        # Re-export backward compatibility classes
        OutboxPublisher = _outbox_legacy.OutboxPublisher
        OutboxWriter = _outbox_legacy.OutboxWriter
        IOutboxPublisher = _outbox_legacy.IOutboxPublisher
        IOutboxWriter = _outbox_legacy.IOutboxWriter
    else:
        raise ImportError("Failed to load backward compatibility module")
else:
    raise ImportError(
        "Backward compatibility module app.core.messaging.outbox.py not found"
    )

__all__ = [
    "OutboxMessage",
    "OutboxMessageStatus",
    "OutboxService",
    "IOutboxService",
    "OutboxDispatcher",
    "IOutboxDispatcher",
    "OutboxPublisherWorker",
    "OutboxWorkerRegistry",
    "outbox_worker_registry",
    "create_outbox_worker",
    # Backward compatibility exports
    "OutboxPublisher",
    "OutboxWriter",
    "IOutboxPublisher",
    "IOutboxWriter",
]
