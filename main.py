# backend/main.py
import logging
from pathlib import Path
from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.security import OAuth2PasswordBearer
from fastapi.openapi.utils import get_openapi
from fastapi.exceptions import RequestValidationError
from starlette.middleware.sessions import SessionMiddleware
from sqlalchemy.orm import Session

from core.config import settings
from database.database import get_db, initialize_database, check_db_health, check_redis_health
from routers import router as api_router

# Configure logging
logger = logging.getLogger(__name__)

# Configure OAuth2 with proper token URL for Swagger UI
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/auth/login",  # Full path to your login endpoint
    scopes={
        "read": "Read access to user data",
        "write": "Write access to user data",
        "admin": "Administrative access"
    }
)

# Initialize database and Redis connections
try:
    initialize_database()
except Exception as e:
    logger.error(f"Failed to initialize database: {e}")
    raise

# Create FastAPI application with enhanced OpenAPI configuration
app = FastAPI(
    title=settings.APP_NAME,
    description="Backend API for MindMate Mental Health System with OAuth2 Authentication",
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    debug=settings.DEBUG,
    # Enhanced OpenAPI configuration for better Swagger UI experience
    openapi_tags=[
        {
            "name": "Authentication",
            "description": "User authentication and authorization endpoints"
        },
        {
            "name": "Users",
            "description": "User management operations"
        },
        {
            "name": "Health",
            "description": "Health check and monitoring endpoints"
        }
    ]
)

# Validation exception handler for better error messages
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle Pydantic validation errors and return user-friendly messages"""
    logger.error(f"Validation error: {exc.errors()}")
    
    # Format validation errors into user-friendly messages
    error_details = []
    for error in exc.errors():
        field = " -> ".join(str(loc) for loc in error["loc"])
        # Extract the actual error message safely
        if error.get("ctx") and hasattr(error["ctx"]["error"], "args"):
            message = str(error["ctx"]["error"])
        else:
            message = error.get("msg", "Validation error")
        error_details.append(f"{field}: {message}")
    
    return JSONResponse(
        status_code=422,
        content={
            "detail": "Validation error",
            "errors": error_details
        }
    )

# Custom OpenAPI schema for better Swagger UI integration
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    
    # Add OAuth2 security scheme
    openapi_schema["components"]["securitySchemes"] = {
        "OAuth2PasswordBearer": {
            "type": "oauth2",
            "flows": {
                "password": {
                    "tokenUrl": "/api/auth/login",
                    "scopes": {
                        "read": "Read access to user data",
                        "write": "Write access to user data",
                        "admin": "Administrative access"
                    }
                }
            }
        },
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT"
        }
    }
    
    # Set global security requirement
    openapi_schema["security"] = [
        {"OAuth2PasswordBearer": []},
        {"BearerAuth": []}
    ]
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

# Add CORS middleware (must be first)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# Add session middleware for OAuth2/cookies
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SECRET_KEY,
    max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
)

# Include API routes
app.include_router(api_router, prefix="/api")

# Global exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions globally."""
    logger.error(f"HTTP Exception on {request.url}: {exc.status_code} - {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "status_code": exc.status_code}
    )

@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions globally."""
    logger.error(f"Unhandled Exception on {request.url}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "An unexpected error occurred",
            "status_code": 500
        }
    )

# Health check endpoints
@app.get(
    "/api/health",
    tags=["Health"],
    summary="Comprehensive Health Check",
    description="Check the health status of the API and its dependencies"
)
async def health_check(db: Session = Depends(get_db)):
    """Comprehensive health check for the API and its dependencies."""
    try:
        health_status = {
            "status": "healthy",
            "timestamp": "2025-01-28T00:00:00Z",  # This would be dynamic in real implementation
            "version": settings.APP_VERSION,
            "checks": {}
        }
        
        # Check database
        db_healthy = check_db_health()
        health_status["checks"]["database"] = {
            "status": "up" if db_healthy else "down",
            "details": "PostgreSQL connection"
        }
        
        # Check Redis
        redis_healthy = check_redis_health()
        health_status["checks"]["redis"] = {
            "status": "up" if redis_healthy else "down",
            "details": "Redis connection for sessions"
        }
        
        # Overall status
        overall_healthy = db_healthy and redis_healthy
        if not overall_healthy:
            health_status["status"] = "degraded"
        
        return health_status
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(
            status_code=500,
            detail="Health check failed"
        )

@app.get(
    "/api/health/ready",
    tags=["Health"],
    summary="Readiness Check",
    description="Kubernetes readiness probe endpoint"
)
async def readiness_check():
    """Readiness probe for container orchestration."""
    try:
        if check_db_health() and check_redis_health():
            return {"status": "ready"}
        else:
            raise HTTPException(status_code=503, detail="Service not ready")
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        raise HTTPException(status_code=503, detail="Service not ready")

@app.get(
    "/api/health/live",
    tags=["Health"],
    summary="Liveness Check",
    description="Kubernetes liveness probe endpoint"
)
async def liveness_check():
    """Liveness probe for container orchestration."""
    return {"status": "alive"}

# Frontend static files configuration
def setup_frontend_serving():
    """Setup static file serving for frontend builds."""
    possible_frontend_paths = [
        Path(__file__).parent / "frontend" / "dist",
        Path(__file__).parent / ".." / "frontend" / "dist",
        Path(__file__).parent / "dist",
        Path(__file__).parent / "build"
    ]
    
    frontend_dist = None
    for path in possible_frontend_paths:
        if path.exists() and path.is_dir():
            frontend_dist = str(path)
            logger.info(f"Found frontend build directory: {frontend_dist}")
            break
    
    if frontend_dist:
        # Mount static files
        app.mount("/static", StaticFiles(directory=frontend_dist), name="static")
        
        # Mount assets for Vite builds
        assets_path = Path(frontend_dist) / "assets"
        if assets_path.exists():
            app.mount("/assets", StaticFiles(directory=str(assets_path)), name="assets")
        
        # Favicon endpoint
        @app.get("/favicon.ico", include_in_schema=False)
        async def favicon():
            favicon_path = Path(frontend_dist) / "favicon.ico"
            if favicon_path.exists():
                return FileResponse(favicon_path)
            raise HTTPException(status_code=404, detail="Favicon not found")
        
        # Root route - serve React app
        @app.get("/", include_in_schema=False)
        async def serve_frontend():
            """Serve the React app at the root route."""
            index_path = Path(frontend_dist) / "index.html"
            if index_path.exists():
                return FileResponse(index_path)
            return JSONResponse(
                content={
                    "message": f"{settings.APP_NAME} Backend API",
                    "version": settings.APP_VERSION,
                    "docs": "/docs",
                    "health": "/api/health"
                }
            )
        
        # Catch-all route for React Router
        @app.get("/{path:path}", include_in_schema=False)
        async def catch_all(path: str):
            """Catch-all route to serve React app for client-side routing."""
            # Don't interfere with API routes
            if path.startswith("api/"):
                raise HTTPException(status_code=404, detail="API endpoint not found")
            
            index_path = Path(frontend_dist) / "index.html"
            if index_path.exists():
                return FileResponse(index_path)
            raise HTTPException(status_code=404, detail="Page not found")
    
    else:
        logger.warning("Frontend build directory not found. Only API will be served.")
        
        @app.get("/", include_in_schema=False)
        async def api_info():
            """API info when frontend is not available."""
            return {
                "message": f"{settings.APP_NAME} Backend API",
                "version": settings.APP_VERSION,
                "docs": "/docs",
                "redoc": "/redoc",
                "health": "/api/health",
                "note": "Frontend not found. Please build your React app first."
            }

# Setup frontend serving
setup_frontend_serving()

# Startup event
@app.on_event("startup")
async def startup_event():
    """Application startup tasks."""
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"Server running on {settings.HOST}:{settings.PORT}")
    logger.info(f"API Documentation: http://localhost:{settings.PORT}/docs")
    logger.info(f"Health Check: http://localhost:{settings.PORT}/api/health")
    logger.info("OAuth2 configuration loaded for Swagger UI")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown tasks."""
    logger.info(f"Shutting down {settings.APP_NAME}")

# Development server
if __name__ == "__main__":
    import uvicorn
    
    logger.info(f"Starting {settings.APP_NAME} development server")
    logger.info(f"Environment: {'Development' if settings.DEBUG else 'Production'}")
    
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        log_level="info" if not settings.DEBUG else "debug",
        reload=settings.DEBUG,
        access_log=True
    )