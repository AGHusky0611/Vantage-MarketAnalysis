"""
Vantage Backend - FastAPI Application Entry Point
"""
import logging
import traceback

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from datetime import datetime

from app.core.config import get_settings
from app.routers import market

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

settings = get_settings()

# ── Create FastAPI App ──────────────────────────────────────────
app = FastAPI(
    title=settings.app_name,
    description="Clear Sight. Smarter Trades. — Institutional-grade analytics for retail traders.",
    version="0.1.0",
)

# ── CORS Middleware (allow Next.js frontend) ────────────────────
# Build allowed origins list (includes production Vercel URL if set)
_origins = [
    settings.frontend_url,
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Global exception handler (ensures CORS headers on 500s) ──
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception on {request.method} {request.url}: {exc}")
    logger.error(traceback.format_exc())
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal server error: {str(exc)}"},
    )

# ── Register Routers ───────────────────────────────────────────
app.include_router(market.router)


# ── Root & Health Endpoints ────────────────────────────────────
@app.get("/")
async def root():
    return {
        "name": "Vantage API",
        "tagline": "Clear Sight. Smarter Trades.",
        "version": "0.1.0",
        "docs": "/docs",
    }


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": "0.1.0",
        "timestamp": datetime.now().isoformat(),
    }
