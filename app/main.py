"""SafeLink AI - FastAPI Application"""
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from .core.config import settings
from .core.database import DatabaseManager
from .core.mqtt_client import mqtt_client
from .endpoints.chatbot import router as chatbot_router, limiter
from .endpoints.webhooks import router as webhooks_router
from .endpoints.analysis import router as analysis_router
from .endpoints.devices import router as devices_router
from .endpoints.mesures import router as mesures_router

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    logger.info(f"Starting {settings.app_name}...")
    
    # Initialize database
    try:
        await DatabaseManager.initialize()
        logger.info("Database initialized")
    except Exception as e:
        logger.error(f"Database init failed: {e}")
    
    # Connect MQTT (optional for development)
    try:
        mqtt_client.connect()
    except Exception as e:
        logger.warning(f"MQTT broker not available (optional for chatbot dev): {e}")
    
    yield
    
    # Cleanup
    logger.info("Shutting down...")
    await DatabaseManager.close()
    mqtt_client.disconnect()


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    description="Chatbot IA pour la cybersécurité IoT SafeLink",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "message": str(exc)}
    )


# Include routers
app.include_router(chatbot_router)
app.include_router(webhooks_router)
app.include_router(analysis_router)
app.include_router(devices_router)
app.include_router(mesures_router)


# Mount static files
static_path = Path(__file__).parent / "static"
if static_path.exists():
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": settings.app_name,
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "chatbot_ui": "/chatbot"
    }


@app.get("/chatbot")
async def chatbot_ui():
    """Serve chatbot test interface"""
    return FileResponse(static_path / "chatbot.html")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug
    )
