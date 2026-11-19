from fastapi import APIRouter, HTTPException, Query, status

from app.config import get_settings
from app.models.constants import LOCATION_CATEGORIES
from app.schemas import CategoryListResponse, LocationSearchResponse
from app.services.locations import (
    search_locations,
    validate_category,
    validate_coordinate,
    validate_query,
)

router = APIRouter(prefix="/api/locations", tags=["Locations"])


@router.get("/categories", response_model=CategoryListResponse)
def categories() -> CategoryListResponse:
    return CategoryListResponse(
        categories=[{"code": code, "label": code.replace("_", " ").title()} for code in LOCATION_CATEGORIES]
    )


@router.get("/search", response_model=LocationSearchResponse)
def search(
    q: str = Query(min_length=1, max_length=80),
    category: str | None = None,
) -> LocationSearchResponse:
    query = validate_query(q, required=True)
    selected = validate_category(category, required=False)
    return LocationSearchResponse(**search_locations(get_settings(), query, selected))


@router.get("/nearby", response_model=LocationSearchResponse)
def nearby(
    category: str = Query(min_length=2, max_length=40),
    q: str | None = Query(default=None, max_length=80),
    lat: float | None = None,
    lng: float | None = None,
) -> LocationSearchResponse:
    selected = validate_category(category, required=True)
    area = validate_query(q, required=False)
    latitude = validate_coordinate(lat, -90, 90, "Latitude")
    longitude = validate_coordinate(lng, -180, 180, "Longitude")
    if (latitude is None) != (longitude is None):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Provide both latitude and longitude, or neither. A village name is enough.",
        )
    # Coordinates are used only to sort this response. They are not stored or returned.
    text = area or selected.replace("_", " ")
    return LocationSearchResponse(**search_locations(get_settings(), text, selected, latitude, longitude))
