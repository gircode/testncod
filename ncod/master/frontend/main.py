"""
Frontend application main module
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import make_asgi_app
from prometheus_fastapi_instrumentator import Instrumentator

from ..core.config import settings

app = FastAPI(
    title="NCOD Frontend",
    description="Network Control and Operation Dashboard Frontend",
    version="1.0.0",
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add Prometheus metrics
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)
Instrumentator().instrument(app).expose(app)
