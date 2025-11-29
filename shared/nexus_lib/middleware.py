import time
import logging
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from prometheus_client import Counter, Histogram

logger = logging.getLogger("nexus.middleware")

REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status'])
REQUEST_LATENCY = Histogram('http_request_duration_seconds', 'HTTP request latency', ['method', 'endpoint'])

class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        try:
            response = await call_next(request)
            status_code = response.status_code
            return response
        except Exception as e:
            status_code = 500
            raise e
        finally:
            duration = time.time() - start_time
            REQUEST_COUNT.labels(method=request.method, endpoint=request.url.path, status=status_code).inc()
            REQUEST_LATENCY.labels(method=request.method, endpoint=request.url.path).observe(duration)

class AuthMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, secret_key: str):
        super().__init__(app)
        self.secret_key = secret_key

    async def dispatch(self, request: Request, call_next):
        # Simplified auth for demo
        return await call_next(request)
