from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.models.constants import CATEGORY_LABELS, COMPLAINT_CATEGORIES
from app.schemas import (
    ComplaintCreate,
    ComplaintCreatedResponse,
    ComplaintListResponse,
    ComplaintResponse,
    StatusUpdateRequest,
    complaint_to_response,
)
from app.security.dependencies import get_current_user, require_administrator
from app.security.rate_limit import rate_limit
from app.services.complaints import create_complaint, get_complaint_for_viewer, list_own_complaints, update_status

router = APIRouter(prefix="/api/complaints", tags=["Complaints"])


@router.post(
    "",
    response_model=ComplaintCreatedResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(rate_limit("complaints", limit=10))],
)
def create(
    body: ComplaintCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ComplaintCreatedResponse:
    complaint = create_complaint(db, user, body)
    payload = complaint_to_response(complaint, include_history=True).model_dump()
    payload["message"] = (
        "Complaint saved in SafeVillage. It has not been submitted to a government department. "
        f"Your tracking ID is {complaint.tracking_id}."
    )
    return ComplaintCreatedResponse(**payload)


@router.get("/categories")
def categories() -> dict:
    return {
        "categories": [{"code": code, "label": CATEGORY_LABELS[code]} for code in COMPLAINT_CATEGORIES],
        "notice": "Categories are for community tracking inside SafeVillage.",
    }


@router.get("", response_model=ComplaintListResponse)
def list_complaints(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> ComplaintListResponse:
    rows = list_own_complaints(db, user)
    return ComplaintListResponse(complaints=[complaint_to_response(row) for row in rows])


@router.get("/{complaint_id}", response_model=ComplaintResponse)
def get_one(
    complaint_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ComplaintResponse:
    complaint = get_complaint_for_viewer(db, complaint_id, user)
    return complaint_to_response(complaint, include_history=True)


@router.patch("/{complaint_id}/status", response_model=ComplaintResponse)
def patch_status(
    complaint_id: str,
    body: StatusUpdateRequest,
    admin: User = Depends(require_administrator),
    db: Session = Depends(get_db),
) -> ComplaintResponse:
    complaint = update_status(db, complaint_id, admin, body.status, body.note)
    return complaint_to_response(complaint, include_history=True)
