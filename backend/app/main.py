"""FastAPI 应用入口。

启动方式（在 backend 目录下）：
    uvicorn app.main:app --reload --port 8000
"""

import logging
from contextlib import asynccontextmanager
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware

from app.api.v1 import auth, life, match, study, system, tags
from app.core.config import settings
from app.core.database import init_db
from app.schemas.common import BusinessError
from app.seed import seed_tags

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    """启动时建表并写入种子数据。"""
    init_db()
    seed_tags()
    logger.info("服务启动完成，AI 开关：%s", settings.AI_ENABLED)
    yield


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="大一新生“破冰·学业·生活”全能赋能平台后端接口",
    lifespan=lifespan,
)


class RequestIdMiddleware(BaseHTTPMiddleware):
    """为每个请求生成 request_id，便于日志串联。"""

    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID") or uuid4().hex
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response


app.add_middleware(RequestIdMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(BusinessError)
async def business_error_handler(request: Request, exc: BusinessError):
    """业务异常统一返回结构。"""
    return JSONResponse(
        status_code=200,
        content={"code": exc.code, "message": exc.message, "data": None},
    )


@app.exception_handler(HTTPException)
async def http_error_handler(request: Request, exc: HTTPException):
    """HTTP 异常也返回统一结构，同时保留状态码。"""
    return JSONResponse(
        status_code=exc.status_code,
        content={"code": exc.status_code, "message": exc.detail, "data": None},
    )


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError):
    """参数校验失败统一返回 40001。"""
    return JSONResponse(
        status_code=200,
        content={"code": 40001, "message": "参数校验失败", "data": exc.errors()},
    )


# 注册业务路由
for router in (auth.router, tags.router, match.router, study.router, life.router, system.router):
    app.include_router(router, prefix=settings.API_PREFIX)

# 上传文件静态访问：/uploads/xxx
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")


@app.get("/")
def root():
    """根路径，返回服务信息。"""
    return {
        "code": 0,
        "message": "ok",
        "data": {
            "app": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "docs": "/docs",
            "api_prefix": settings.API_PREFIX,
        },
    }