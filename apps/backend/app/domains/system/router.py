from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from app.core.context import current_request_id
from app.core.error_codes import ErrorCode
from app.core.exceptions import AppException
from app.core.health import check_readiness
from app.core.response import ResponseModel, success_response

from .schemas import SystemStatus

router = APIRouter(prefix="/system", tags=["系统"])


@router.get("/status", response_model=ResponseModel[SystemStatus], summary="获取公共系统状态")
async def get_system_status(request: Request) -> ResponseModel[SystemStatus]:
    resources = getattr(request.app.state, "resources", None)
    settings = getattr(request.app.state, "settings", None)
    if resources is None or settings is None:
        raise AppException(
            status_code=503,
            code=ErrorCode.SERVICE_UNAVAILABLE,
            message="服务尚未就绪",
        )
    result = await check_readiness(resources, settings)
    if not result.ready:
        raise AppException(
            status_code=503,
            code=ErrorCode.SERVICE_UNAVAILABLE,
            message="服务暂时不可用",
        )
    return success_response(data=SystemStatus(status="available"), request_id=current_request_id())


def readiness_response(*, status_code: int, status: str, checks: dict[str, str]) -> JSONResponse:
    return JSONResponse(status_code=status_code, content={"status": status, "checks": checks})
