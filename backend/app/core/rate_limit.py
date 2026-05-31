"""滑动窗口限流中间件 — 内存实现"""

import time
import logging
from collections import defaultdict

from fastapi import Request, HTTPException

logger = logging.getLogger(__name__)


class RateLimiter:
    """基于内存的滑动窗口限流器"""

    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        # {key: [timestamp, timestamp, ...]}
        self._requests: dict[str, list[float]] = defaultdict(list)

    def _cleanup(self, key: str, now: float) -> None:
        """清理窗口外的旧记录"""
        cutoff = now - self.window_seconds
        self._requests[key] = [
            ts for ts in self._requests[key] if ts > cutoff
        ]

    def check(self, key: str) -> bool:
        """检查是否超过限流，返回 True 表示允许"""
        now = time.time()
        self._cleanup(key, now)
        if len(self._requests[key]) >= self.max_requests:
            return False
        self._requests[key].append(now)
        return True

    def remaining(self, key: str) -> int:
        """返回剩余可用请求数"""
        now = time.time()
        self._cleanup(key, now)
        return max(0, self.max_requests - len(self._requests[key]))


# 全局限流器实例
rate_limiter = RateLimiter(max_requests=100, window_seconds=60)


async def rate_limit_middleware(request: Request, call_next):
    """限流中间件"""
    # 获取限流 key（优先用 API Key，fallback 到 IP）
    api_key = request.headers.get("X-API-Key", "")
    if not api_key:
        auth = request.headers.get("Authorization", "")
        if auth.startswith("Bearer "):
            api_key = auth[7:]
    limit_key = api_key or request.client.host if request.client else "unknown"

    # 健康检查不限流
    if request.url.path == "/api/health":
        return await call_next(request)

    if not rate_limiter.check(limit_key):
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded: {rate_limiter.max_requests} requests per {rate_limiter.window_seconds}s",
        )

    response = await call_next(request)
    response.headers["X-RateLimit-Remaining"] = str(rate_limiter.remaining(limit_key))
    return response
