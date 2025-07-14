from fastapi import APIRouter, status
from schemas import PingResponse
from decorators import with_logging
import logging

router = APIRouter(tags=["Health Check"])
logger = logging.getLogger(__name__)

@router.get("/ping", response_model=PingResponse, status_code=status.HTTP_200_OK)
@with_logging
async def ping() -> PingResponse:
    """
    Health-check style endpoint.
    Returns JSON: {"message": "pong"}.
    """
    return PingResponse(message="pong")
