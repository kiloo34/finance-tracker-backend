"""
auth package — public API

Exposes get_current_user, require_admin, and related utilities so
routers can do:  from .. import auth  →  auth.get_current_user
"""
from .jwt import (
    get_current_user,
    require_admin,
    get_session_id_from_token,
    create_access_token,
    generate_session_id,
    oauth2_scheme,
)

__all__ = [
    "get_current_user",
    "require_admin",
    "get_session_id_from_token",
    "create_access_token",
    "generate_session_id",
    "oauth2_scheme",
]
