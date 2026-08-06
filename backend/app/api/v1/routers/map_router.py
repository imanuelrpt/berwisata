from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db_session
from app.controllers import map_controller
from app.schemas.common import ApiResponse
from app.schemas.location import RouteRequest

router = APIRouter(prefix="/maps", tags=["Maps & Routes"])


@router.post("/route", response_model=ApiResponse)
def get_route(payload: RouteRequest, db: Session = Depends(get_db_session)):
    return ApiResponse(data=map_controller.get_route(db, payload))
