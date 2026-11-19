from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Complaint, EmergencyContact, User
from app.models.constants import CATEGORY_LABELS
from app.schemas import (
    AdminUserResponse,
    ComplaintResponse,
    DashboardResponse,
    EmergencyContactResponse,
    EmergencyContactWrite,
    StatusUpdateRequest,
    complaint_to_response,
)
from app.security.dependencies import require_administrator
from app.services.complaints import list_all_complaints, update_status

router = APIRouter(prefix="/api/admin", tags=["Administration"])


@router.get("/dashboard", response_model=DashboardResponse)
def dashboard(admin: User = Depends(require_administrator), db: Session = Depends(get_db)) -> DashboardResponse:
    total_citizens = db.scalar(select(func.count()).select_from(User).where(User.role == "citizen")) or 0
    total_complaints = db.scalar(select(func.count()).select_from(Complaint)) or 0
    pending = db.scalar(select(func.count()).select_from(Complaint).where(Complaint.status == "pending")) or 0
    resolved = db.scalar(select(func.count()).select_from(Complaint).where(Complaint.status == "resolved")) or 0
    grouped = db.execute(select(Complaint.category, func.count()).group_by(Complaint.category)).all()
    recent = list_all_complaints(db)[:8]
    return DashboardResponse(
        total_citizens=total_citizens,
        total_complaints=total_complaints,
        pending_complaints=pending,
        resolved_complaints=resolved,
        complaints_by_category={CATEGORY_LABELS.get(category, category): count for category, count in grouped},
        recent_complaints=[complaint_to_response(item) for item in recent],
    )


@router.get("/users", response_model=list[AdminUserResponse])
def users(_: User = Depends(require_administrator), db: Session = Depends(get_db)) -> list[User]:
    return list(db.scalars(select(User).order_by(User.created_at.desc())).all())


@router.get("/complaints", response_model=list[ComplaintResponse])
def complaints(_: User = Depends(require_administrator), db: Session = Depends(get_db)) -> list[ComplaintResponse]:
    return [complaint_to_response(item) for item in list_all_complaints(db)]


@router.patch("/complaints/{complaint_id}", response_model=ComplaintResponse)
def patch_complaint(
    complaint_id: str,
    body: StatusUpdateRequest,
    admin: User = Depends(require_administrator),
    db: Session = Depends(get_db),
) -> ComplaintResponse:
    complaint = update_status(db, complaint_id, admin, body.status, body.note)
    return complaint_to_response(complaint, include_history=True)


@router.post("/emergency-contacts", response_model=EmergencyContactResponse, status_code=status.HTTP_201_CREATED)
def add_contact(
    body: EmergencyContactWrite,
    _: User = Depends(require_administrator),
    db: Session = Depends(get_db),
) -> EmergencyContact:
    contact = EmergencyContact(
        name=body.name,
        phone=body.phone,
        description=body.description + " Informational only. SafeVillage does not dispatch this service.",
        category=body.category.lower(),
        state=body.state,
        district=body.district,
        is_national=False,
        is_informational=True,
    )
    db.add(contact)
    db.commit()
    db.refresh(contact)
    return contact


@router.patch("/emergency-contacts/{contact_id}", response_model=EmergencyContactResponse)
def update_contact(
    contact_id: int,
    body: EmergencyContactWrite,
    _: User = Depends(require_administrator),
    db: Session = Depends(get_db),
) -> EmergencyContact:
    contact = db.get(EmergencyContact, contact_id)
    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found.")
    if contact.is_national and body.phone != contact.phone:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="National emergency numbers cannot be changed in this demo.",
        )
    contact.name = body.name
    contact.description = body.description
    contact.category = body.category.lower()
    contact.state = body.state
    contact.district = body.district
    if not contact.is_national:
        contact.phone = body.phone
    contact.is_informational = True
    db.commit()
    db.refresh(contact)
    return contact
