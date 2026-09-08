"""Vercel ASGI entrypoint for the FastAPI control-plane API."""

from backend.app.main import app

__all__ = ["app"]
