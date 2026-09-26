from contextlib import asynccontextmanager
from concurrent.futures import ThreadPoolExecutor

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from middleware.request_id import RequestIdMiddleware
from middleware.logging_middleware import LoggingMiddleware
from api.routes import router as api_router
from api.health import router as health_router
from infrastructure.mission_registry import MissionRegistry

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Server"] = "" # Hide server info
        return response

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.executor = ThreadPoolExecutor(max_workers=5)
    app.state.mission_registry = MissionRegistry()
    yield
    app.state.executor.shutdown(wait=True)

app = FastAPI(title="ADRIE API", version="1.0.0", lifespan=lifespan)

# Middlewares (Order matters: outer to inner)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(LoggingMiddleware)
app.add_middleware(RequestIdMiddleware)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include Routers
app.include_router(health_router, tags=["Health"])
app.include_router(api_router)
