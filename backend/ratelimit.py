"""Shared rate limiter instance for FastAPI routes.

Import `limiter` from here in both `main.py` (to attach to `app.state` and
register the exception handler) and in route modules that decorate endpoints
with `@limiter.limit(...)`. Keeping it in its own module avoids a circular
import between `main` and the route packages.
"""
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
