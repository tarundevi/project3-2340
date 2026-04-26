from fastapi import APIRouter, Depends

from app.services.auth import require_role
from app.services.usage_logger import get_logs, get_stats

router = APIRouter(prefix="/api/admin")


@router.get("/logs")
def list_logs(limit: int = 100, _: dict = Depends(require_role("admin"))):
    return get_logs(limit=limit)


@router.get("/stats")
def usage_stats(_: dict = Depends(require_role("admin"))):
    return get_stats()
