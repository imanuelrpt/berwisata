from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.api.deps import get_db_session, get_optional_user, get_current_admin
from app.controllers import destination_controller
from app.schemas.common import ApiResponse
from app.schemas.destination import DestinationCreate, DestinationUpdate
from app.schemas.search import SearchRequest

router = APIRouter(prefix="/destinations", tags=["Destinations"])


@router.get("", response_model=ApiResponse)
def list_destinations(
    page: int = 1,
    per_page: int = 12,
    query: str | None = None,
    province: str | None = None,
    regency: str | None = None,
    category: str | None = None,
    request: Request = None,
    db: Session = Depends(get_db_session),
    user=Depends(get_optional_user),
):
    result = destination_controller.list_destinations(db, request, page, per_page, query, province, regency, category, user)
    return ApiResponse(data=result)


@router.post("/search", response_model=ApiResponse)
def search_destinations(
    payload: SearchRequest,
    request: Request = None,
    use_ors: bool = False,
    db: Session = Depends(get_db_session),
    user=Depends(get_optional_user),
):
    result = destination_controller.search_destinations(db, request, payload, user, use_ors)
    return ApiResponse(data=result)


@router.get("/nearby", response_model=ApiResponse)
def nearby(
    latitude: float,
    longitude: float,
    radius_km: float = 50,
    limit: int = 10,
    db: Session = Depends(get_db_session),
    user=Depends(get_optional_user),
):
    result = destination_controller.nearby_destinations(db, None, latitude, longitude, radius_km, limit, user)
    return ApiResponse(data=result)


@router.get("/{destination_id}", response_model=ApiResponse)
def get_destination(destination_id: int, db: Session = Depends(get_db_session), user=Depends(get_optional_user)):
    result = destination_controller.get_destination_detail(db, destination_id, user)
    return ApiResponse(data=result)


@router.get("/{destination_id}/route", response_model=ApiResponse)
def get_destination_route(
    destination_id: int,
    latitude: float,
    longitude: float,
    transport: str = "car",
    db: Session = Depends(get_db_session),
):
    result = destination_controller.get_destination_route(db, destination_id, latitude, longitude, transport)
    return ApiResponse(data=result)


@router.post("", response_model=ApiResponse, status_code=201)
def create_destination(payload: DestinationCreate, db: Session = Depends(get_db_session), admin=Depends(get_current_admin)):
    return ApiResponse(message="Destinasi dibuat", data=destination_controller.create_destination(db, payload))


@router.patch("/{destination_id}", response_model=ApiResponse)
def update_destination(destination_id: int, payload: DestinationUpdate, db: Session = Depends(get_db_session), admin=Depends(get_current_admin)):
    return ApiResponse(message="Destinasi diperbarui", data=destination_controller.update_destination(db, destination_id, payload))


@router.delete("/{destination_id}", response_model=ApiResponse)
def delete_destination(destination_id: int, db: Session = Depends(get_db_session), admin=Depends(get_current_admin)):
    return ApiResponse(message="Destinasi dihapus", data=destination_controller.delete_destination(db, destination_id))
