"""统一响应结构与分页辅助。"""

from typing import Any


def success(data: Any = None, message: str = "ok") -> dict[str, Any]:
    """统一成功响应：{code:0, message, data}。"""
    return {"code": 0, "message": message, "data": data}


def failure(code: int, message: str, data: Any = None) -> dict[str, Any]:
    """统一业务失败响应。"""
    return {"code": code, "message": message, "data": data}


def paginate(items: list[Any], total: int, page: int, page_size: int) -> dict[str, Any]:
    """统一分页结构。"""
    return {"items": items, "total": total, "page": page, "page_size": page_size}


class BusinessError(Exception):
    """业务异常：由全局异常处理器转换为统一失败响应。"""

    def __init__(self, code: int = 40001, message: str = "业务处理失败") -> None:
        self.code = code
        self.message = message
        super().__init__(message)