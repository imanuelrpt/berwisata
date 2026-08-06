from sqlalchemy.orm import Session

from app.schemas.location import RouteRequest
from app.services import destination_service
from app.services.map_service import get_route
from app.services.weather_service import get_weather


def get_weather_for_coords(latitude: float, longitude: float, force: bool = False) -> dict:
    return get_weather(latitude, longitude, force_refresh=force)


def get_weather_for_destination(db: Session, destination_id: int, force: bool = False) -> dict:
    dest = destination_service.get_destination_or_404(db, destination_id)
    data = get_weather(dest.latitude, dest.longitude, force_refresh=force)
    data["destination_id"] = destination_id
    data["destination_name"] = dest.name
    return data


def get_route(db: Session, payload: RouteRequest) -> dict:
    dest = destination_service.get_destination_or_404(db, payload.destination_id)
    if payload.latitude is None or payload.longitude is None:
        raise ValueError("Koordinat user diperlukan")
    route = get_route(
        payload.latitude, payload.longitude, dest.latitude, dest.longitude, payload.transport if payload.transport else payload.model
    )
    route["destination_id"] = dest.id
    route["destination_name"] = dest.name
    return route
