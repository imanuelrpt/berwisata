from typing import Optional

from fastapi import Request
from sqlalchemy.orm import Session

from app.models import User
from app.repositories.destination_repository import DestinationRepository
from app.repositories.favorite_repository import FavoriteRepository
from app.schemas.destination import DestinationCreate, DestinationUpdate
from app.schemas.search import SearchRequest
from app.services import destination_service
from app.services.map_service import get_route
from app.services.weather_service import get_weather
from app.utils.geo import haversine_km


def list_destinations(
    db: Session,
    request: Request,
    page: int,
    per_page: int,
    query: Optional[str],
    province: Optional[str],
    regency: Optional[str],
    category: Optional[str],
    user: Optional[User],
) -> dict:
    favorites = FavoriteRepository(db).ids_by_user(user.id) if user else []
    rows, total = destination_service.search_destinations(
        db,
        page=page,
        per_page=per_page,
        query=query,
        province=province,
        regency=regency,
        category_slug=category,
    )
    data = [destination_service.serialize_destination(d) for d in rows]
    latitude, longitude = _coords_from_request(request)
    data = destination_service.enrich_with_weather_and_distance(data, latitude, longitude, user, set(favorites))
    return {"data": data, "meta": _meta(page, per_page, total)}


def search_destinations(
    db: Session,
    request: Request,
    payload: SearchRequest,
    user: Optional[User],
    use_ors: bool = False,
) -> dict:
    favorites = FavoriteRepository(db).ids_by_user(user.id) if user else []
    latitude = payload.latitude
    longitude = payload.longitude
    if latitude is None and longitude is None:
        latitude, longitude = _coords_from_request(request)

    rows, total = destination_service.search_destinations(
        db,
        page=payload.page,
        per_page=payload.per_page,
        query=payload.query,
        province=payload.province,
        regency=payload.regency,
        category_id=payload.category_id,
        category_slug=payload.category_slug,
        min_price=payload.min_price,
        max_price=payload.max_price,
        min_rating=payload.min_rating,
        is_free=payload.is_free,
        radius_km=payload.radius_km,
        latitude=latitude,
        longitude=longitude,
        budget=payload.budget,
        is_open_now=payload.is_open_now,
        facilities=payload.facilities,
        tags=payload.tags,
        audience=payload.audience,
        min_hidden_gem_score=payload.min_hidden_gem_score,
        sort_by=payload.sort_by,
        order=payload.order,
    )
    data = [destination_service.serialize_destination(d) for d in rows]
    data = destination_service.enrich_with_weather_and_distance(data, latitude, longitude, user, set(favorites))

    if latitude is not None and longitude is not None:
        for d in data:
            d["duration_minutes"] = round((d["distance_km"] or 0) / 55.0 * 60.0, 1)
    return {"data": data, "meta": _meta(payload.page, payload.per_page, total)}


def get_destination_detail(db: Session, destination_id: int, user: Optional[User]) -> dict:
    dest = destination_service.get_destination_or_404(db, destination_id)
    repo = DestinationRepository(db)
    repo.increment_views(dest)
    db.commit()

    data = destination_service.serialize_destination(dest, include_weather=True, include_description=True)
    if user:
        data["is_favorited"] = FavoriteRepository(db).get_by_user_and_dest(user.id, destination_id) is not None
    data["weather"] = get_weather(dest.latitude, dest.longitude)
    return data


def get_destination_route(db: Session, destination_id: int, latitude: float, longitude: float, transport: str) -> dict:
    dest = destination_service.get_destination_or_404(db, destination_id)
    route = get_route(latitude, longitude, dest.latitude, dest.longitude, transport)
    route["destination_id"] = destination_id
    route["destination_name"] = dest.name
    return route


def nearby_destinations(db: Session, request: Request, latitude: float, longitude: float, radius_km: float, limit: int, user: Optional[User]) -> dict:
    favorites = FavoriteRepository(db).ids_by_user(user.id) if user else []
    rows, _ = destination_service.search_destinations(
        db,
        page=1,
        per_page=limit,
        radius_km=radius_km,
        latitude=latitude,
        longitude=longitude,
        sort_by="distance",
        order="asc",
    )
    data = [destination_service.serialize_destination(d) for d in rows]
    data = destination_service.enrich_with_weather_and_distance(data, latitude, longitude, user, set(favorites))
    return {"data": data}


def create_destination(db: Session, payload: DestinationCreate) -> dict:
    dest = destination_service.create_destination(db, payload)
    return {"destination": destination_service.serialize_destination(dest, include_description=True)}


def update_destination(db: Session, destination_id: int, payload: DestinationUpdate) -> dict:
    dest = destination_service.get_destination_or_404(db, destination_id)
    dest = destination_service.update_destination(db, dest, payload)
    return {"destination": destination_service.serialize_destination(dest, include_description=True)}


def delete_destination(db: Session, destination_id: int) -> dict:
    dest = destination_service.get_destination_or_404(db, destination_id)
    destination_service.delete_destination(db, dest)
    return {"message": "Destinasi dihapus"}


def _coords_from_request(request: Request) -> tuple[Optional[float], Optional[float]]:
    lat = request.headers.get("x-user-lat")
    lon = request.headers.get("x-user-lon")
    try:
        return (float(lat), float(lon)) if lat and lon else (None, None)
    except ValueError:
        return (None, None)


def _meta(page: int, per_page: int, total: int) -> dict:
    pages = max(1, (total + per_page - 1) // per_page)
    return {
        "page": page,
        "per_page": per_page,
        "total": total,
        "pages": pages,
        "has_next": page < pages,
        "has_prev": page > 1,
    }
