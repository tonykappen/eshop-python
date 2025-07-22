"""Main FastAPI application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from eshop.config.settings import settings
from eshop.core.di.container import Container
from eshop.core.logging.logger import configure_logging, get_logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger = get_logger("main")
    logger.info("Starting eShop Modular Monolith application")
    
    # Configure logging
    configure_logging(
        log_level=settings.log_level,
        seq_url=settings.seq_url,
        enable_console=settings.log_enable_console,
        enable_seq=settings.log_enable_seq
    )
    
    # Initialize DI container
    app.state.container = Container()
    app.state.container.config.from_dict({
        "database": {
            "connection_string": settings.database_connection_string
        },
        "redis": {
            "connection_string": settings.redis_connection_string
        },
        "rabbitmq": {
            "connection_string": settings.rabbitmq_connection_string
        },
        "keycloak": {
            "server_url": settings.keycloak_server_url,
            "realm": settings.keycloak_realm,
            "client_id": settings.keycloak_client_id,
            "client_secret": settings.keycloak_client_secret
        }
    })
    
    # Scan for services
    # scanner = app.state.container.assembly_scanner()
    # scanner.scan_directory("eshop/modules", "eshop.modules")
    
    logger.info("Application startup complete")
    
    yield
    
    # Shutdown
    logger.info("Shutting down eShop Modular Monolith application")


# Create FastAPI app
app = FastAPI(
    title=settings.name,
    version=settings.version,
    debug=settings.debug,
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": f"{settings.name} (Python/FastAPI)",
        "version": settings.version,
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


# Import and include module routers
# Note: These will be added as we implement each module
# from modules.catalog.api import router as catalog_router
# from modules.basket.api import router as basket_router
# from modules.ordering.api import router as ordering_router

# app.include_router(catalog_router, prefix="/catalog", tags=["catalog"])
# app.include_router(basket_router, prefix="/basket", tags=["basket"])
# app.include_router(ordering_router, prefix="/ordering", tags=["ordering"])


def run():
    """Run the application."""
    import uvicorn
    
    uvicorn.run(
        "eshop.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )


if __name__ == "__main__":
    run() 