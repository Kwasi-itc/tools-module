from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
import logging
from app.config import settings
from app.api.v1 import tools, registry, executions, permissions, analytics

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Tools Module API",
    description="Dynamic tool registry and execution system for intelligent agents",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add validation error handler to log detailed errors
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Log validation errors with full details for debugging"""
    errors = exc.errors()
    body_str = None
    if exc.body:
        try:
            body_str = exc.body.decode('utf-8') if isinstance(exc.body, bytes) else str(exc.body)
        except Exception:
            body_str = "<unable to decode body>"
    
    error_details = {
        "detail": errors,
        "body": body_str
    }
    logger.error(
        f"Validation error on {request.method} {request.url.path}: {errors}",
        extra={"request_body": body_str, "errors": errors}
    )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=error_details
    )

# Register API routers
app.include_router(tools.router, prefix=settings.api_v1_prefix)
app.include_router(registry.router, prefix=settings.api_v1_prefix)
app.include_router(executions.router, prefix=settings.api_v1_prefix)
app.include_router(permissions.router, prefix=settings.api_v1_prefix)
app.include_router(analytics.router, prefix=settings.api_v1_prefix)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Tools Module API",
        "version": "1.0.0",
        "docs": "/docs",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "tools-module",
    }


@app.get("/health/ready")
async def readiness_check():
    """Readiness check endpoint - can be extended to check database connectivity"""
    return {
        "status": "ready",
    }


@app.get("/health/live")
async def liveness_check():
    """Liveness check endpoint"""
    return {
        "status": "alive",
    }

