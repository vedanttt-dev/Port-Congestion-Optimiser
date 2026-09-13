"""Liveness probe used by the frontend shell and the P1 exit-criterion test."""

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict:
    """Report service liveness."""
    return {"status": "ok"}
