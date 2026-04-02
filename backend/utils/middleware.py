"""
SmartSafety+ - Audit Trail Middleware
Logs every mutating API request (POST/PUT/DELETE) with user, IP, endpoint, and timestamp.
Read-only (GET) requests are not logged to avoid noise.
"""
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from datetime import datetime, timezone
from config import db, logger
import uuid
import json


class AuditTrailMiddleware(BaseHTTPMiddleware):
    """Log mutating API actions for compliance and traceability."""

    # Only log state-changing methods
    AUDITABLE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}

    # Skip noisy or non-business endpoints
    SKIP_PATHS = {"/api/health", "/api/dashboard/stats", "/api/dashboard/charts",
                  "/api/dashboard/recent-activity", "/api/notifications",
                  "/docs", "/openapi.json", "/redoc"}

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # Only audit mutations
        if request.method not in self.AUDITABLE_METHODS:
            return response

        path = request.url.path
        if any(path.startswith(skip) for skip in self.SKIP_PATHS):
            return response

        try:
            # Extract user from JWT (best-effort, don't block on failure)
            user_info = await self._extract_user(request)

            audit_entry = {
                "id": str(uuid.uuid4()),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "method": request.method,
                "path": path,
                "query_params": dict(request.query_params),
                "status_code": response.status_code,
                "ip_address": self._get_client_ip(request),
                "user_agent": request.headers.get("user-agent", "")[:200],
                "user_id": user_info.get("id"),
                "user_email": user_info.get("email"),
                "user_role": user_info.get("role"),
            }

            # Fire-and-forget insert (don't slow down the response)
            await db.audit_log.insert_one(audit_entry)

        except Exception as e:
            # Never let audit logging break the actual request
            logger.warning(f"Audit log error: {e}")

        return response

    async def _extract_user(self, request: Request) -> dict:
        """Try to extract user info from the Authorization header."""
        try:
            import jwt as pyjwt
            from config import JWT_SECRET, JWT_ALGORITHM

            auth = request.headers.get("authorization", "")
            if auth.startswith("Bearer "):
                token = auth[7:]
                payload = pyjwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
                return {
                    "id": payload.get("sub"),
                    "email": payload.get("email"),
                    "role": payload.get("role"),
                }
        except Exception:
            pass
        return {}

    def _get_client_ip(self, request: Request) -> str:
        """Get real client IP, respecting proxy headers."""
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        return request.client.host if request.client else "unknown"
