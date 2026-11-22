from fastapi import FastAPI, Request, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import os
import logging
from app.config import settings
from app.database import db_manager
from app.seed_data import seed_database
from app.routers import (
    auth, incidents, ai, analytics, reports, ws, feedback, audit, model_ops,
    sla, notifications, public, service_feedback
)
from app.utils.security import (
    SecurityHeadersMiddleware,
    auth_rate_limiter,
    ai_rate_limiter,
    general_rate_limiter
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("encrowatch.main")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Validate environment configuration
    env_warnings = settings.validate_environment()
    for w in env_warnings:
        logger.warning(f"Environment Notice: {w}")

    # Connect DB and Seed data
    logger.info("Initializing EncroWatch AI platform backend...")
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    os.makedirs(os.path.join(settings.UPLOAD_DIR, "original"), exist_ok=True)
    os.makedirs(os.path.join(settings.UPLOAD_DIR, "annotated"), exist_ok=True)
    os.makedirs(os.path.join(settings.UPLOAD_DIR, "privacy"), exist_ok=True)
    os.makedirs(os.path.join(settings.UPLOAD_DIR, "inspections"), exist_ok=True)
    os.makedirs(os.path.join(settings.UPLOAD_DIR, "reports"), exist_ok=True)

    await db_manager.connect()
    await seed_database()
    logger.info("EncroWatch AI platform is online and ready!")
    yield
    # Shutdown
    await db_manager.close()
    logger.info("EncroWatch AI platform shutdown complete.")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.PROJECT_VERSION,
    description="AI-Powered Urban Accessibility and Road & Footpath Encroachment Monitoring System",
    lifespan=lifespan
)

# 1. Security Headers Middleware (Batch 5 Hardening)
app.add_middleware(SecurityHeadersMiddleware)

# 2. Narrow CORS Middleware for Authorized Application Origins (Batch 5/6 Hardening)
ALLOWED_ORIGINS = settings.allowed_origins_list

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept", "Origin", "X-Requested-With"],
)

# 3. Rate Limiting and Request Size Limiting Middleware (Batch 5 Hardening)
@app.middleware("http")
async def security_rate_and_size_limiter(request: Request, call_next):
    # Client identifier
    client_ip = request.client.host if request.client else "127.0.0.1"
    path = request.url.path

    # Maximum payload size check (50MB for video/multi-image, 25MB standard)
    content_length = request.headers.get("content-length")
    if content_length:
        try:
            cl = int(content_length)
            if cl > 50 * 1024 * 1024:
                return JSONResponse(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    content={"detail": "Request payload exceeds maximum allowable limit of 50 MB."}
                )
        except ValueError:
            pass

    # Endpoint-specific rate limiting
    if path.startswith("/api/auth/login"):
        if auth_rate_limiter.is_rate_limited(client_ip):
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={"detail": "Rate limit exceeded: Too many authentication attempts. Please retry in 1 minute."}
            )
    elif path.startswith("/api/ai/"):
        if ai_rate_limiter.is_rate_limited(client_ip):
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={"detail": "Rate limit exceeded on AI computer vision endpoint. Please retry shortly."}
            )
    elif path.startswith("/api/"):
        if general_rate_limiter.is_rate_limited(client_ip):
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={"detail": "API rate limit exceeded. Please throttle requests."}
            )

    return await call_next(request)

# Global Request Validation Exception Handler
# Formats Pydantic validation errors into clean strings so frontend never receives raw unhandled dicts
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = []
    for err in exc.errors():
        field = ".".join(str(l) for l in err.get("loc", []) if l != "body")
        msg = err.get("msg", "Validation error")
        errors.append(f"{field}: {msg}" if field else msg)
    clean_message = "; ".join(errors) if errors else "Invalid request data"
    logger.warning(f"Validation error on {request.url.path}: {clean_message}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": clean_message, "errors": exc.errors()}
    )

# Static files for original, annotated, and inspection uploads
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

# Mount API Routers
app.include_router(auth.router, prefix=settings.API_V1_STR)
app.include_router(incidents.router, prefix=settings.API_V1_STR)
app.include_router(ai.router, prefix=settings.API_V1_STR)
app.include_router(analytics.router, prefix=settings.API_V1_STR)
app.include_router(reports.router, prefix=settings.API_V1_STR)
app.include_router(feedback.router, prefix=settings.API_V1_STR)
app.include_router(audit.router, prefix=settings.API_V1_STR)
app.include_router(model_ops.router, prefix=settings.API_V1_STR)
app.include_router(sla.router, prefix=settings.API_V1_STR)
app.include_router(notifications.router, prefix=settings.API_V1_STR)
app.include_router(public.router, prefix=settings.API_V1_STR)
app.include_router(service_feedback.router, prefix=settings.API_V1_STR)
app.include_router(ws.router)

@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "platform": settings.PROJECT_NAME,
        "version": settings.PROJECT_VERSION,
        "database_mode": db_manager.mode,
        "ai_engine": "OpenCV-Vision-Pipeline + Modular-YOLO-Hook",
        "security_hardened": True
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
