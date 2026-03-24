"""
Global rate limiter instance.

Kept in its own module to avoid circular imports between main.py and routers.
Import this anywhere rate limiting is needed:
    from app.core.limiter import limiter
"""
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
