from fastapi import APIRouter, Depends, Query
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import EmergencyContact
from app.schemas import EmergencyListResponse

router = APIRouter(prefix="/api/emergency", tags=["Emergency information"])

DISCLAIMER = (
    "These numbers are public information. SafeVillage does not dispatch police, fire, or ambulance services. "
    "Call the number yourself. Availability can differ by state and district."
)


@router.get("/contacts", response_model=EmergencyListResponse)
def contacts(
    district: str | None = Query(default=None, max_length=80),
    state: str | None = Query(default=None, max_length=80),
    db: Session = Depends(get_db),
) -> EmergencyListResponse:
    statement = select(EmergencyContact).where(EmergencyContact.is_national.is_(True))
    if district or state:
        local = select(EmergencyContact).where(EmergencyContact.is_national.is_(False))
        if district:
            local = local.where(EmergencyContact.district.ilike(district.strip()))
        if state:
            local = local.where(EmergencyContact.state.ilike(state.strip()))
        national = db.scalars(statement.order_by(EmergencyContact.phone)).all()
        extra = db.scalars(local.order_by(EmergencyContact.name)).all()
        rows = list(national) + list(extra)
    else:
        rows = list(db.scalars(select(EmergencyContact).order_by(EmergencyContact.is_national.desc(), EmergencyContact.phone)).all())
    return EmergencyListResponse(live_dispatch=False, disclaimer=DISCLAIMER, contacts=rows)
