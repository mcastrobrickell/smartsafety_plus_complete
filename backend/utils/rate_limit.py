"""
SmartSafety+ - Rate Limiting
Uses slowapi to protect sensitive endpoints from abuse.

Usage in routers:
    from utils.rate_limit import limiter
    
    @router.post("/auth/login")
    @limiter.limit("10/minute")
    async def login(request: Request, ...):
        ...
"""
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request
from fastapi.responses import JSONResponse


def _key_func(request: Request) -> str:
    """Rate limit by IP address, respecting proxy headers."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return get_remote_address(request)


# Global limiter instance
limiter = Limiter(
    key_func=_key_func,
    default_limits=["200/minute"],       # Global default
    storage_uri="memory://",             # In-memory (use Redis URI for production)
)


async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    """Custom handler for rate limit exceeded errors."""
    return JSONResponse(
        status_code=429,
        content={
            "detail": "Demasiadas solicitudes. Intenta de nuevo más tarde.",
            "retry_after": str(exc.detail),
        }
    )
