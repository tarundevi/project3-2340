from fastapi import APIRouter

from app.services.usage_logger import get_logs, get_stats

router = APIRouter(prefix="/api/admin")


@router.get("/logs")
def list_logs(limit: int = 100):
    return get_logs(limit=limit)


@router.get("/stats")
def usage_stats():
    return get_stats()
