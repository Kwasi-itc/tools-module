from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.api.v1 import tools, registry, executions, permissions, analytics

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

