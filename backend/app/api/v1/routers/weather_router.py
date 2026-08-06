from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db_session
from app.controllers import map_controller
from app.schemas.common import ApiResponse

router = APIRouter(prefix="/weather", tags=["Weather"])


@router.get("", response_model=ApiResponse)
def weather(latitude: float, longitude: float, force: bool = False):
    return ApiResponse(data=map_controller.get_weather_for_coords(latitude, longitude, force))


@router.get("/destination/{destination_id}", response_model=ApiResponse)
def weather_for_destination(destination_id: int, force: bool = False, db: Session = Depends(get_db_session)):
    return ApiResponse(data=map_controller.get_weather_for_destination(db, destination_id, force))
