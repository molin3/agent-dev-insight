"""FastAPI 主应用入口"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import datasets, evaluations, experiments, health, scores, traces, ws
from app.api.public import generations as public_generations
from app.api.public import scores as public_scores
from app.api.public import spans as public_spans
from app.api.public import traces as public_traces
from app.core.config import settings
from app.core.database import close_db, init_db
from app.core.redis import close_redis, init_redis

logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    await init_redis()
    logger.info("%s v%s started", settings.app_name, settings.app_version)
    yield
    await close_redis()
    await close_db()
    logger.info("Application shutdown")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Agent 评估与可观测性平台",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 统一错误响应格式
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "code": exc.status_code,
            "message": str(exc.detail),
            "data": None,
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled exception: %s", exc, exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "code": 500,
            "message": "Internal server error",
            "data": None,
        },
    )

app.include_router(health.router, prefix="/api", tags=["健康检查"])

# 公共 API（LangFuse 兼容）
app.include_router(public_traces.router, prefix="/api/public", tags=["Public API"])
app.include_router(public_spans.router, prefix="/api/public", tags=["Public API"])
app.include_router(public_generations.router, prefix="/api/public", tags=["Public API"])
app.include_router(public_scores.router, prefix="/api/public", tags=["Public API"])

# 内部 API
app.include_router(traces.router, prefix="/api", tags=["Traces"])
app.include_router(scores.router, prefix="/api", tags=["Scores"])
app.include_router(evaluations.router, prefix="/api", tags=["Evaluations"])
app.include_router(datasets.router, prefix="/api", tags=["Datasets"])
app.include_router(experiments.router, prefix="/api", tags=["Experiments"])
app.include_router(ws.router, tags=["WebSocket"])


@app.get("/")
async def root():
    return {
        "code": 200,
        "message": "success",
        "data": {
            "name": settings.app_name,
            "version": settings.app_version,
            "docs": "/docs",
        },
    }
