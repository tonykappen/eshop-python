# Cancellation Token Implementation Guide
## FastAPI to .NET CancellationToken Parity

**Document Version:** 1.0  
**Last Updated:** October 9, 2025  
**Author:** Technical Documentation Team

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [.NET CancellationToken Background](#net-cancellationtoken-background)
3. [FastAPI Implementation](#fastapi-implementation)
4. [API Parity Comparison](#api-parity-comparison)
5. [Database Rollback Integration](#database-rollback-integration)
6. [Request Disconnection Handling](#request-disconnection-handling)
7. [Usage Patterns](#usage-patterns)
8. [Complete Flow Diagrams](#complete-flow-diagrams)
9. [Best Practices](#best-practices)
10. [Testing Cancellation](#testing-cancellation)

---

## 🎯 Overview

This document explains how **CancellationToken** functionality from .NET has been implemented in FastAPI with **1-to-1 parity**. The implementation provides the same benefits as .NET:

### ✅ Key Features

1. **Request Disconnection Detection** - Automatically detects when clients disconnect
2. **Database Transaction Rollback** - Automatic rollback on cancellation
3. **Manual Cancellation** - Programmatic cancellation support
4. **Callback System** - Register custom cleanup functions
5. **Async Operation Support** - Full asyncio integration
6. **Resource Efficiency** - Stop processing when client is gone

### 🎪 Why This Matters

Without cancellation tokens:
- ❌ Orphaned database transactions
- ❌ Wasted CPU/memory on disconnected requests
- ❌ Potential data corruption from partial updates
- ❌ No graceful shutdown mechanism

With cancellation tokens:
- ✅ Automatic cleanup on client disconnect
- ✅ Database integrity maintained
- ✅ Resource efficiency
- ✅ Familiar .NET patterns for migrating teams

---

## 🔍 .NET CancellationToken Background

### .NET Implementation

In .NET, `CancellationToken` is a struct that provides cooperative cancellation:

```csharp
// .NET Handler Example
public class CreateProductHandler : IRequestHandler<CreateProductCommand, Product>
{
    private readonly IProductRepository _repository;
    
    public async Task<Product> Handle(
        CreateProductCommand request, 
        CancellationToken cancellationToken)
    {
        // Check if cancellation was requested
        cancellationToken.ThrowIfCancellationRequested();
        
        // Perform database operation
        var product = new Product 
        { 
            Name = request.Name, 
            Price = request.Price 
        };
        
        await _repository.AddAsync(product, cancellationToken);
        
        return product;
    }
}
```

### .NET Key Properties/Methods

| Member | Type | Description |
|--------|------|-------------|
| `IsCancellationRequested` | Property | Gets whether cancellation has been requested |
| `ThrowIfCancellationRequested()` | Method | Throws `OperationCanceledException` if cancelled |
| `Register(Action)` | Method | Registers a callback for cancellation |
| `CanBeCanceled` | Property | Gets whether the token can be cancelled |

### .NET Cancellation Sources

```csharp
// Creating cancellation sources in .NET
using var cts = new CancellationTokenSource();
var token = cts.Token;

// Cancel after timeout
cts.CancelAfter(TimeSpan.FromSeconds(30));

// Manual cancellation
cts.Cancel();
```

---

## 🐍 FastAPI Implementation

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI Request                           │
└───────────────────────┬─────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────────┐
│  CancellationToken Created (via Dependency Injection)        │
│  • Monitors request.is_disconnected()                        │
│  • Attaches to database session (if provided)                │
└───────────────────────┬─────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────────┐
│  Background Monitoring Task Started                          │
│  • Polls every 100ms for disconnection                       │
│  • Sets _cancelled flag when detected                        │
└───────────────────────┬─────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────────┐
│  Handler Execution                                           │
│  • Checks token.is_cancellation_requested                    │
│  • Calls token.throw_if_cancellation_requested()             │
│  • Performs business logic                                   │
└───────────────────────┬─────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────────┐
│  On Cancellation or Exception                                │
│  • Cleanup() called in finally block                         │
│  • Execute rollback callbacks                                │
│  • Rollback database session if attached                     │
└─────────────────────────────────────────────────────────────┘
```

### Core Implementation

**File:** `backend/app/core/mediator/cancellation.py`

```python
class CancellationToken:
    """Cancellation token equivalent to .NET CancellationToken."""
    
    def __init__(
        self, 
        request: Request | None = None, 
        session: AsyncSession | None = None
    ) -> None:
        """Initialize cancellation token with optional database session."""
        self._request = request
        self._session = session
        self._cancelled = False
        self._logger = BaseLogger(__name__)
        self._monitor_task: asyncio.Task[None] | None = None
        self._rollback_callbacks: list[callable] = []
        
        # Start monitoring for request disconnection
        if request:
            self._start_monitoring()
    
    def _start_monitoring(self) -> None:
        """Start monitoring for request cancellation."""
        if self._request:
            self._monitor_task = asyncio.create_task(
                self._monitor_disconnection()
            )
    
    async def _monitor_disconnection(self) -> None:
        """Monitor for request disconnection."""
        try:
            while not self._cancelled and self._request is not None:
                # FastAPI's request.is_disconnected() checks client connection
                if await self._request.is_disconnected():
                    self._cancelled = True
                    self._logger.log_debug_with_context(
                        "Request disconnected, cancellation token triggered"
                    )
                    break
                await asyncio.sleep(0.1)  # Check every 100ms
        except Exception as e:
            self._logger.log_error_with_context(
                "Error monitoring request disconnection", error=e
            )
            self._cancelled = True
```

### Key Features

#### 1. Request Monitoring
- Polls `request.is_disconnected()` every 100ms
- Non-blocking background task
- Automatically sets cancellation flag

#### 2. Database Session Integration
- Accepts optional `AsyncSession` parameter
- Automatically rolls back on cancellation
- Prevents orphaned transactions

#### 3. Callback System
- Register cleanup functions
- Executed on cancellation or cleanup
- Supports both sync and async callbacks

---

## 🔄 API Parity Comparison

### Complete API Mapping

| .NET CancellationToken | FastAPI CancellationToken | Notes |
|------------------------|---------------------------|-------|
| `IsCancellationRequested` | `is_cancellation_requested` | Property, same behavior |
| `ThrowIfCancellationRequested()` | `throw_if_cancellation_requested()` | Method, raises `CancellationError` |
| `Register(Action callback)` | `register_rollback_callback(callback)` | Supports async callbacks too |
| `CanBeCanceled` | Always `True` | All tokens can be cancelled |
| N/A | `cancel()` | Manual cancellation trigger |
| N/A | `cleanup()` | Explicit cleanup method |
| N/A | `wait_for_cancellation()` | Async wait for cancellation |
| N/A | `execute_with_rollback(operation)` | Execute with automatic rollback |
| N/A | `set_session(session)` | Set/attach database session |
| N/A | `get_session()` | Get attached session |

### Side-by-Side Code Comparison

#### .NET Code
```csharp
public async Task<Product> Handle(
    CreateProductCommand request,
    CancellationToken cancellationToken)
{
    // Check for cancellation
    cancellationToken.ThrowIfCancellationRequested();
    
    // Check property
    if (cancellationToken.IsCancellationRequested)
    {
        return null;
    }
    
    // Register callback
    cancellationToken.Register(() => 
    {
        Console.WriteLine("Cancelled!");
    });
    
    // Perform operation
    var product = await _repository.CreateAsync(request);
    return product;
}
```

#### FastAPI Code (Equivalent)
```python
async def handle(
    self,
    request: CreateProductCommand,
    cancellation_token: CancellationToken
) -> Product:
    # Check for cancellation
    cancellation_token.throw_if_cancellation_requested()
    
    # Check property
    if cancellation_token.is_cancellation_requested:
        return None
    
    # Register callback
    cancellation_token.register_rollback_callback(
        lambda: print("Cancelled!")
    )
    
    # Perform operation
    product = await self.repository.create(request)
    return product
```

### Exception Parity

| .NET | FastAPI | Raised When |
|------|---------|-------------|
| `OperationCanceledException` | `CancellationError` | `ThrowIfCancellationRequested()` called while cancelled |

---

## 🗄️ Database Rollback Integration

### Three-Layer Rollback Strategy

The implementation has **three layers** of database rollback protection:

#### Layer 1: CancellationToken Internal Rollback

**File:** `backend/app/core/mediator/cancellation.py`

```python
async def _rollback_session(self) -> None:
    """Rollback the associated database session."""
    if self._session:
        try:
            await self._session.rollback()
            self._logger.log_debug_with_context(
                "Database session rolled back due to cancellation"
            )
        except Exception as e:
            self._logger.log_error_with_context(
                "Error rolling back database session", error=e
            )

async def cleanup(self) -> None:
    """Clean up monitoring task and execute rollback if cancelled."""
    if self._cancelled:
        await self._execute_rollback_callbacks()
    
    if self._monitor_task and not self._monitor_task.done():
        self._monitor_task.cancel()
        with suppress(asyncio.CancelledError):
            await self._monitor_task

async def _execute_rollback_callbacks(self) -> None:
    """Execute all registered rollback callbacks."""
    for callback in self._rollback_callbacks:
        try:
            if asyncio.iscoroutinefunction(callback):
                await callback()
            else:
                callback()
        except Exception as e:
            self._logger.log_error_with_context(
                "Error executing rollback callback", error=e
            )
```

**When it triggers:**
- Cancellation detected (client disconnect)
- Manual `cancel()` called
- `cleanup()` called in finally block

#### Layer 2: Session Manager Exception Handler

**File:** `backend/app/core/database/session_with_cancellation.py`

```python
async def get_db_session_with_cancellation(
    request: Request,
) -> AsyncGenerator[tuple[AsyncSession, CancellationToken], None]:
    """Get database session with integrated cancellation token."""
    async with AsyncSessionLocal() as session:
        cancellation_token = get_cancellation_token_with_session(request, session)
        
        try:
            yield session, cancellation_token
        except Exception as e:
            # Layer 2: Exception-based rollback
            logger.log_error_with_context(
                "Database operation failed, rolling back transaction", error=e
            )
            await session.rollback()
            raise
        finally:
            # Cleanup cancellation token (triggers Layer 1 if cancelled)
            await cancellation_token.cleanup()
```

**When it triggers:**
- Any exception raised during operation
- Explicit exception handling

#### Layer 3: Transaction Manager Smart Rollback

```python
@asynccontextmanager
async def db_transaction_with_cancellation(
    request: Request,
) -> AsyncGenerator[tuple[AsyncSession, CancellationToken], None]:
    """Database transaction with cancellation token integration."""
    async with AsyncSessionLocal() as session:
        cancellation_token = get_cancellation_token_with_session(request, session)
        
        try:
            await session.begin()
            yield session, cancellation_token
            
            # Layer 3: Smart commit/rollback based on cancellation state
            if not cancellation_token.is_cancellation_requested:
                await session.commit()
                logger.log_debug_with_context(
                    "Database transaction committed successfully"
                )
            else:
                await session.rollback()
                logger.log_debug_with_context(
                    "Database transaction rolled back due to cancellation"
                )
                
        except Exception as e:
            # Layer 2: Exception-based rollback
            logger.log_error_with_context(
                "Database transaction failed, rolling back", error=e
            )
            await session.rollback()
            raise
        finally:
            # Layer 1: Cleanup (triggers callback rollback if needed)
            await cancellation_token.cleanup()
```

**When it triggers:**
- Checks cancellation state before commit
- Rolls back if cancelled
- Exception rollback as fallback

### Rollback Decision Matrix

| Scenario | Layer 1 | Layer 2 | Layer 3 | Result |
|----------|---------|---------|---------|--------|
| Client disconnects | ✅ Detects | ⏭️ Skipped | ⏭️ Skipped | Rollback via cleanup |
| Exception raised | ⏭️ Skipped | ✅ Catches | ⏭️ Skipped | Immediate rollback |
| Manual cancel() | ✅ Triggers | ⏭️ Skipped | ⏭️ Skipped | Callback rollback |
| Normal completion, not cancelled | ⏭️ Skipped | ⏭️ Skipped | ✅ Commits | Transaction committed |
| Normal completion, but cancelled | ✅ Detects | ⏭️ Skipped | ✅ Checks flag | Rollback before commit |

### Complete Rollback Flow

```
┌─────────────────────────────────────────────────────────────┐
│ TRIGGER EVENT                                                │
│ • Client Disconnects                                         │
│ • Exception Raised                                           │
│ • Manual cancel()                                            │
│ • Timeout                                                    │
└───────────────────────┬─────────────────────────────────────┘
                        ↓
        ┌───────────────────────────────┐
        │ Is this an Exception?         │
        └────┬──────────────────┬────────┘
             │ YES              │ NO
             ↓                  ↓
    ┌────────────────┐   ┌──────────────────┐
    │ Layer 2:       │   │ Layer 1:         │
    │ Immediate      │   │ Monitor detects  │
    │ Rollback       │   │ Sets _cancelled  │
    │ in except{}    │   │ = True           │
    └────────┬───────┘   └────────┬─────────┘
             │                    │
             └────────┬───────────┘
                      ↓
         ┌─────────────────────────────┐
         │ finally: cleanup() called   │
         └────────────┬────────────────┘
                      ↓
         ┌─────────────────────────────┐
         │ Is _cancelled == True?      │
         └────┬──────────────────┬─────┘
              │ YES              │ NO
              ↓                  ↓
    ┌──────────────────┐   ┌──────────────┐
    │ Execute          │   │ No action    │
    │ _rollback_       │   │ needed       │
    │ callbacks()      │   │              │
    └────────┬─────────┘   └──────────────┘
             ↓
    ┌──────────────────┐
    │ For each         │
    │ callback:        │
    │ • _rollback_     │
    │   _session()     │
    │ • Custom         │
    │   callbacks      │
    └────────┬─────────┘
             ↓
    ┌──────────────────┐
    │ await session    │
    │ .rollback()      │
    └────────┬─────────┘
             ↓
    ┌──────────────────┐
    │ Database rolled  │
    │ back!            │
    └──────────────────┘
```

---

## 🔌 Request Disconnection Handling

### How FastAPI Detects Disconnection

FastAPI's `Request` object provides `is_disconnected()` method:

```python
async def _monitor_disconnection(self) -> None:
    """Monitor for request disconnection."""
    while not self._cancelled and self._request is not None:
        # This is the key FastAPI feature
        if await self._request.is_disconnected():
            self._cancelled = True
            break
        await asyncio.sleep(0.1)  # Poll every 100ms
```

### Under the Hood

FastAPI's `is_disconnected()`:
1. Checks if the underlying ASGI connection is still active
2. Detects TCP connection closure
3. Handles HTTP/1.1 and HTTP/2 properly
4. Returns `True` when client disconnects

### Polling Interval Trade-offs

| Interval | Pro | Con |
|----------|-----|-----|
| 10ms | Very fast detection | High CPU usage |
| 100ms (current) | Good balance | Up to 100ms delay |
| 1000ms | Low CPU usage | Slow detection |

**Current choice: 100ms** - Good balance for most use cases.

### Testing Disconnection

You can test disconnection behavior:

```python
import asyncio
from fastapi.testclient import TestClient

def test_cancellation_on_disconnect():
    """Test that cancellation triggers on client disconnect."""
    
    async def long_running_operation():
        # Simulate long operation
        await asyncio.sleep(10)
    
    with TestClient(app) as client:
        # Start request
        response = client.post("/products", json={...})
        
        # Simulate disconnect by closing client
        # Cancellation token should detect this
```

---

## 💡 Usage Patterns

### Pattern 1: Basic Handler with Cancellation Check

```python
from app.core.mediator.handler_registry import IRequestHandler
from app.core.mediator.cancellation import CancellationToken

class GetProductsHandler(IRequestHandler[GetProductsQuery, List[Product]]):
    def __init__(self, repository: IProductRepository):
        self.repository = repository
    
    async def handle(
        self,
        query: GetProductsQuery,
        cancellation_token: CancellationToken
    ) -> List[Product]:
        # Check before expensive operation
        cancellation_token.throw_if_cancellation_requested()
        
        # Perform database query
        products = await self.repository.get_all()
        
        return products
```

### Pattern 2: Handler with Database Session and Cancellation

```python
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database.session_with_cancellation import (
    get_db_session_with_cancellation
)

@router.post("/products")
async def create_product(
    request: CreateProductRequest,
    session_and_token: tuple[AsyncSession, CancellationToken] = Depends(
        get_db_session_with_cancellation
    )
):
    session, cancellation_token = session_and_token
    
    # If client disconnects, session will automatically rollback
    product = Product(**request.dict())
    session.add(product)
    await session.commit()
    
    return product
```

### Pattern 3: Long-Running Operation with Periodic Checks

```python
class ProcessBatchHandler(IRequestHandler[ProcessBatchCommand, BatchResult]):
    async def handle(
        self,
        command: ProcessBatchCommand,
        cancellation_token: CancellationToken
    ) -> BatchResult:
        results = []
        
        for item in command.items:
            # Check before each item
            cancellation_token.throw_if_cancellation_requested()
            
            # Process item
            result = await self.process_item(item)
            results.append(result)
        
        return BatchResult(results=results)
```

### Pattern 4: Custom Rollback Callbacks

```python
class CreateOrderHandler(IRequestHandler[CreateOrderCommand, Order]):
    async def handle(
        self,
        command: CreateOrderCommand,
        cancellation_token: CancellationToken
    ) -> Order:
        # Register custom cleanup
        temp_files = []
        
        async def cleanup_temp_files():
            for file in temp_files:
                await file.delete()
        
        cancellation_token.register_rollback_callback(cleanup_temp_files)
        
        # Process order
        order = await self.create_order(command)
        
        # Generate invoice PDF
        invoice_file = await self.generate_invoice(order)
        temp_files.append(invoice_file)
        
        return order
```

### Pattern 5: Transaction with Explicit Commit Control

```python
from app.core.database.session_with_cancellation import (
    db_transaction_with_cancellation
)

async def complex_multi_step_operation(request: Request):
    async with db_transaction_with_cancellation(request) as (session, token):
        # Step 1: Create product
        token.throw_if_cancellation_requested()
        product = Product(name="Widget")
        session.add(product)
        
        # Step 2: Create inventory record
        token.throw_if_cancellation_requested()
        inventory = Inventory(product_id=product.id, quantity=100)
        session.add(inventory)
        
        # Step 3: Create audit log
        token.throw_if_cancellation_requested()
        audit = AuditLog(action="product_created")
        session.add(audit)
        
        # Transaction commits automatically if not cancelled
        # Rolls back automatically if cancelled or exception raised
```

### Pattern 6: Dependency Injection in Endpoints

```python
from fastapi import APIRouter, Depends, Request
from app.core.mediator.fastapi_integration import (
    get_mediator_dependency,
    get_cancellation_token_dependency
)

router = APIRouter()

# Method 1: Inject token separately
@router.post("/products")
async def create_product(
    request: CreateProductRequest,
    mediator: IMediator = Depends(get_mediator_dependency),
    cancellation_token: CancellationToken = Depends(
        get_cancellation_token_dependency
    )
):
    command = CreateProductCommand(**request.dict())
    result = await mediator.send(command, cancellation_token)
    return result

# Method 2: Use session with integrated token
@router.get("/products")
async def get_products(
    session_and_token: tuple[AsyncSession, CancellationToken] = Depends(
        get_db_session_with_cancellation
    )
):
    session, token = session_and_token
    token.throw_if_cancellation_requested()
    
    result = await session.execute(select(Product))
    products = result.scalars().all()
    return products
```

### Pattern 7: Manual Cancellation for Business Rules

```python
class ValidateInventoryHandler(IRequestHandler[ValidateInventoryCommand, bool]):
    async def handle(
        self,
        command: ValidateInventoryCommand,
        cancellation_token: CancellationToken
    ) -> bool:
        # Check inventory
        inventory = await self.repository.get_inventory(command.product_id)
        
        if inventory.quantity < command.requested_quantity:
            # Business rule violation - cancel the operation
            cancellation_token.cancel()
            raise BusinessRuleError("Insufficient inventory")
        
        return True
```

---

## 📊 Complete Flow Diagrams

### End-to-End Request Flow with Cancellation

```
┌─────────────────────────────────────────────────────────────┐
│ 1. Client Sends Request                                      │
│    POST /api/products                                        │
└───────────────────────┬─────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────────┐
│ 2. FastAPI Endpoint (Dependency Injection)                   │
│    • get_mediator_dependency()                               │
│    • get_cancellation_token_dependency(request)              │
│    • get_db_session_with_cancellation(request)               │
└───────────────────────┬─────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────────┐
│ 3. CancellationToken Created                                 │
│    token = CancellationToken(request, session)               │
│    • _monitor_task starts polling is_disconnected()          │
│    • _session attached for rollback                          │
└───────────────────────┬─────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────────┐
│ 4. Mediator.send(command, token)                             │
│    • ValidationBehavior checks cancellation                  │
│    • LoggingBehavior checks cancellation                     │
└───────────────────────┬─────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────────┐
│ 5. Handler.handle(command, token)                            │
│    • token.throw_if_cancellation_requested()                 │
│    • Perform business logic                                  │
│    • Database operations                                     │
└───────────────────────┬─────────────────────────────────────┘
                        ↓
           ┌────────────────────────────┐
           │ Did Client Disconnect?     │
           └─────┬──────────────┬───────┘
                 │ YES          │ NO
                 ↓              ↓
    ┌────────────────────┐  ┌──────────────────┐
    │ Monitor detects    │  │ Complete         │
    │ disconnection      │  │ successfully     │
    │ • _cancelled=True  │  │ • Commit DB      │
    │ • Continue handler │  │ • Return result  │
    └─────┬──────────────┘  └────────┬─────────┘
          ↓                          ↓
    ┌────────────────────┐  ┌──────────────────┐
    │ Next check throws  │  │ 6. Return        │
    │ CancellationError  │  │    Response      │
    └─────┬──────────────┘  │    to Client     │
          ↓                 └──────────────────┘
    ┌────────────────────┐
    │ finally: cleanup() │
    │ • Execute rollback │
    │   callbacks        │
    │ • session.rollback│
    └────────┬───────────┘
             ↓
    ┌────────────────────┐
    │ Exception handler  │
    │ catches            │
    │ CancellationError  │
    │ • Returns 499 or   │
    │   logs gracefully  │
    └────────────────────┘
```

### Parallel Processing: Monitor Task vs Handler Task

```
Time →
────────────────────────────────────────────────────────────────

Handler Task:
│
├─ Token Created
├─ Monitor Started ────────┐
├─ Validation              │
├─ Business Logic          │ Monitor Task:
├─ DB Query 1              │ │
├─ DB Query 2              │ ├─ Check disconnected? (100ms)
├─ DB Query 3              │ ├─ Check disconnected? (200ms)
│                          │ ├─ Client Disconnects! ──┐
│                          │ ├─ Check disconnected? ──┤ TRUE
│                          │ ├─ Set _cancelled=True   │
│                          │ └─ Task ends             │
├─ Check cancellation ─────┼──────────────────────────┘
│  throw_if_requested() ───┤ Sees _cancelled==True
│  ❌ Raises Error         │
└─ finally: cleanup() ─────┘
   └─ Rollback DB
```

### Database Session Lifecycle

```
┌─────────────────────────────────────────────────────────────┐
│ Context Manager Entered                                      │
│ async with get_db_session_with_cancellation(request)         │
└───────────────────────┬─────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────────┐
│ Session Created                                              │
│ session = AsyncSessionLocal()                                │
└───────────────────────┬─────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────────┐
│ Token Created with Session                                   │
│ token = get_cancellation_token_with_session(request, session)│
│ • token._session = session                                   │
│ • Monitor started                                            │
└───────────────────────┬─────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────────┐
│ Yield to Handler                                             │
│ yield session, cancellation_token                            │
└───────────────────────┬─────────────────────────────────────┘
                        ↓
           ┌────────────────────────────┐
           │ Handler Execution          │
           │ • session.add(...)         │
           │ • session.execute(...)     │
           └─────┬──────────────┬───────┘
                 │ Exception    │ Success
                 ↓              ↓
    ┌────────────────────┐  ┌──────────────────┐
    │ except Exception:  │  │ No exception     │
    │ • Log error        │  │ • Session auto-  │
    │ • session.rollback │  │   commits (or    │
    │ • raise            │  │   explicit)      │
    └─────┬──────────────┘  └────────┬─────────┘
          │                          │
          └────────┬─────────────────┘
                   ↓
┌─────────────────────────────────────────────────────────────┐
│ finally: Cleanup                                             │
│ await cancellation_token.cleanup()                           │
│ • If _cancelled: execute rollback callbacks                  │
│ • Stop monitor task                                          │
└───────────────────────┬─────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────────┐
│ Context Manager Exits                                        │
│ • Session closed automatically (async with)                  │
│ • All resources cleaned up                                   │
└─────────────────────────────────────────────────────────────┘
```

---

## ✅ Best Practices

### 1. Always Check Before Expensive Operations

```python
async def handle(self, query: SearchQuery, token: CancellationToken):
    # ✅ Good: Check before expensive operation
    token.throw_if_cancellation_requested()
    results = await self.expensive_search(query)
    
    # ❌ Bad: Never check
    results = await self.expensive_search(query)  # Might waste resources
```

### 2. Use Appropriate Session Manager

```python
# ✅ Good: Use get_db_session_with_cancellation for write operations
@router.post("/products")
async def create(
    session_and_token = Depends(get_db_session_with_cancellation)
):
    session, token = session_and_token
    # Automatic rollback on cancellation

# ✅ Good: Use db_transaction_with_cancellation for multi-step transactions
async def complex_operation(request: Request):
    async with db_transaction_with_cancellation(request) as (session, token):
        # Multiple operations in transaction
        # Automatic commit if successful, rollback if cancelled

# ❌ Bad: Manual session without cancellation token
session = AsyncSessionLocal()
# No automatic rollback on disconnect
```

### 3. Check Periodically in Long Operations

```python
async def handle(self, command: ProcessBatchCommand, token: CancellationToken):
    results = []
    
    for i, item in enumerate(command.items):
        # ✅ Good: Check every N iterations
        if i % 10 == 0:
            token.throw_if_cancellation_requested()
        
        result = await self.process(item)
        results.append(result)
    
    return results
```

### 4. Register Cleanup for External Resources

```python
async def handle(self, command: ExportCommand, token: CancellationToken):
    temp_file = await create_temp_file()
    
    # ✅ Good: Register cleanup
    async def cleanup():
        await temp_file.delete()
    
    token.register_rollback_callback(cleanup)
    
    # Process...
    # If cancelled, temp_file automatically deleted
```

### 5. Don't Swallow Cancellation Errors

```python
async def handle(self, query: GetDataQuery, token: CancellationToken):
    try:
        token.throw_if_cancellation_requested()
        data = await self.get_data()
        return data
    except CancellationError:
        # ❌ Bad: Swallow and continue
        return None  # This prevents proper cleanup!
    
    # ✅ Good: Let it propagate
    token.throw_if_cancellation_requested()
    data = await self.get_data()
    return data
```

### 6. Use Context Managers for Token Lifecycle

```python
# ✅ Good: Use context manager
async with create_cancellation_token(request, session) as token:
    await process_data(token)
# Cleanup automatic

# ❌ Bad: Manual management
token = CancellationToken(request, session)
await process_data(token)
# Forgot to call cleanup()!
```

### 7. Test Cancellation Behavior

```python
@pytest.mark.asyncio
async def test_handler_respects_cancellation():
    """Test that handler stops when cancelled."""
    token = CancellationToken()
    handler = GetProductsHandler()
    
    # Cancel before execution
    token.cancel()
    
    # Should raise CancellationError
    with pytest.raises(CancellationError):
        await handler.handle(query, token)
```

### 8. Log Cancellation Events

```python
async def handle(self, command: Command, token: CancellationToken):
    try:
        token.throw_if_cancellation_requested()
        result = await self.process(command)
        return result
    except CancellationError:
        # ✅ Good: Log before re-raising
        self.logger.log_info_with_context(
            "Operation cancelled by client",
            context={"command": type(command).__name__}
        )
        raise
```

### 9. Don't Check Too Frequently

```python
async def handle(self, command: ProcessCommand, token: CancellationToken):
    # ❌ Bad: Check every iteration in tight loop
    for item in million_items:
        token.throw_if_cancellation_requested()  # Too frequent!
        process(item)
    
    # ✅ Good: Check periodically
    for i, item in enumerate(million_items):
        if i % 1000 == 0:  # Every 1000 items
            token.throw_if_cancellation_requested()
        process(item)
```

### 10. Document Cancellation Behavior

```python
class ProcessOrderHandler:
    """
    Process an order and create invoice.
    
    Cancellation Behavior:
    - If cancelled before payment: No database changes
    - If cancelled after payment: Payment rolled back
    - Temp invoice files cleaned up on cancellation
    """
    
    async def handle(
        self, 
        command: ProcessOrderCommand,
        cancellation_token: CancellationToken
    ) -> Order:
        # Implementation...
```

---

## 🧪 Testing Cancellation

### Unit Test: Basic Cancellation

```python
import pytest
from app.core.mediator.cancellation import CancellationToken, CancellationError

@pytest.mark.asyncio
async def test_cancellation_token_basic():
    """Test basic cancellation token functionality."""
    token = CancellationToken()
    
    # Initially not cancelled
    assert not token.is_cancellation_requested
    
    # Cancel it
    token.cancel()
    
    # Now cancelled
    assert token.is_cancellation_requested
    
    # Should throw
    with pytest.raises(CancellationError):
        token.throw_if_cancellation_requested()
```

### Unit Test: Callback Execution

```python
@pytest.mark.asyncio
async def test_rollback_callbacks():
    """Test that rollback callbacks are executed."""
    token = CancellationToken()
    
    callback_executed = []
    
    def callback():
        callback_executed.append(True)
    
    token.register_rollback_callback(callback)
    token.cancel()
    
    await token.cleanup()
    
    assert len(callback_executed) == 1
```

### Integration Test: Database Rollback

```python
@pytest.mark.asyncio
async def test_database_rollback_on_cancellation():
    """Test that database rolls back on cancellation."""
    async with AsyncSessionLocal() as session:
        token = CancellationToken(session=session)
        
        # Add a product
        product = Product(name="Test", price=100)
        session.add(product)
        await session.flush()
        
        # Cancel before commit
        token.cancel()
        await token.cleanup()
        
        # Session should be rolled back
        # Product should not exist
        result = await session.execute(
            select(Product).where(Product.name == "Test")
        )
        assert result.scalar_one_or_none() is None
```

### Integration Test: Request Disconnection

```python
@pytest.mark.asyncio
async def test_request_disconnection_detection():
    """Test that token detects request disconnection."""
    
    class MockRequest:
        def __init__(self):
            self.disconnected = False
        
        async def is_disconnected(self):
            return self.disconnected
    
    mock_request = MockRequest()
    token = CancellationToken(request=mock_request)
    
    # Initially not cancelled
    assert not token.is_cancellation_requested
    
    # Simulate disconnection
    mock_request.disconnected = True
    
    # Wait for monitor to detect (max 200ms)
    await asyncio.sleep(0.2)
    
    # Should be cancelled now
    assert token.is_cancellation_requested
    
    await token.cleanup()
```

### End-to-End Test: Handler with Cancellation

```python
@pytest.mark.asyncio
async def test_handler_with_cancellation(test_client):
    """Test full request flow with cancellation."""
    
    # Start a long-running request
    async def long_request():
        response = await test_client.post(
            "/api/products/batch",
            json={"count": 10000}
        )
        return response
    
    # Start request
    task = asyncio.create_task(long_request())
    
    # Wait a bit
    await asyncio.sleep(0.1)
    
    # Cancel the task (simulates client disconnect)
    task.cancel()
    
    # Task should be cancelled
    with pytest.raises(asyncio.CancelledError):
        await task
```

### Mock Test: Expensive Operation Cancelled

```python
@pytest.mark.asyncio
async def test_expensive_operation_not_executed():
    """Test that expensive operation is not executed if cancelled."""
    
    expensive_called = []
    
    async def expensive_operation():
        expensive_called.append(True)
        await asyncio.sleep(1)
    
    token = CancellationToken()
    token.cancel()
    
    # Handler
    async def handle():
        token.throw_if_cancellation_requested()
        await expensive_operation()
    
    # Should raise before expensive operation
    with pytest.raises(CancellationError):
        await handle()
    
    # Expensive operation never called
    assert len(expensive_called) == 0
```

---

## 📝 Summary

### What We've Achieved

1. ✅ **Full .NET Parity** - API matches `CancellationToken` behavior
2. ✅ **Automatic Detection** - Monitors client disconnection
3. ✅ **Database Safety** - Three layers of rollback protection
4. ✅ **Resource Efficiency** - Stops processing on disconnect
5. ✅ **Easy Integration** - Dependency injection pattern
6. ✅ **Extensible** - Callback system for custom cleanup

### Key Files

| File | Purpose |
|------|---------|
| `app/core/mediator/cancellation.py` | Core `CancellationToken` implementation |
| `app/core/database/session_with_cancellation.py` | Database integration |
| `app/core/mediator/fastapi_integration.py` | Dependency injection helpers |
| `app/modules/*/handlers/*.py` | Handler implementations using tokens |

### When to Use What

| Use Case | Pattern | Session Type |
|----------|---------|--------------|
| Read-only query | Basic token | No session needed |
| Single write | `get_db_session_with_cancellation` | Auto-rollback session |
| Multi-step transaction | `db_transaction_with_cancellation` | Explicit transaction |
| Background job | `get_global_cancellation_token` | Manual session |
| Long-running batch | Periodic checks + callbacks | Choose based on writes |

### Migration from .NET Checklist

- [ ] Replace `CancellationToken` parameter with `CancellationToken`
- [ ] Change `IsCancellationRequested` to `is_cancellation_requested`
- [ ] Change `ThrowIfCancellationRequested()` to `throw_if_cancellation_requested()`
- [ ] Replace `Register()` with `register_rollback_callback()`
- [ ] Add `async`/`await` to handler methods
- [ ] Use dependency injection for token creation
- [ ] Add periodic checks in long loops
- [ ] Test disconnection behavior

---

## 🎓 Further Reading

- [FastAPI Request Documentation](https://fastapi.tiangolo.com/advanced/using-request-directly/)
- [SQLAlchemy Async Sessions](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)
- [Python asyncio Cancellation](https://docs.python.org/3/library/asyncio-task.html#task-cancellation)
- [.NET CancellationToken](https://learn.microsoft.com/en-us/dotnet/api/system.threading.cancellationtoken)

---

**Document End**

For questions or issues, please refer to the development team or create a GitHub issue.

