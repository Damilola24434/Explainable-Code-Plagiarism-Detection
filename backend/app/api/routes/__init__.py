from fastapi import APIRouter

from app.api.routes.collections import router as collections_router
from app.api.routes.datasets import router as datasets_router
from app.api.routes.runs import router as runs_router

router = APIRouter()

router.include_router(collections_router)
router.include_router(datasets_router)
router.include_router(runs_router)

__all__ = ["router"]
