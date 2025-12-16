"""Configuration of routers for all endpoints."""

from fastapi import APIRouter

from app.api.endpoints.report import router_v1 as report_router_v1

router = APIRouter()

# -- API --
router.include_router(report_router_v1)
