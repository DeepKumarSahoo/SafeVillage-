"""Create demo users, schemes, emergency contacts, and one sample complaint."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.data.demo_content import EMERGENCY_CONTACTS, SCHEMES, UNVERIFIED
from app.models import Complaint, ComplaintStatusHistory, EmergencyContact, GovernmentScheme, User
from app.security.passwords import hash_password


def _user(db: Session, *, email: str, password: str, full_name: str, role: str, village: str | None) -> User:
    existing = db.scalar(select(User).where(User.email == email.lower()))
    if existing:
        return existing
    user = User(
        full_name=full_name,
        email=email.lower(),
        hashed_password=hash_password(password),
        role=role,
        village=village,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def seed_database(db: Session) -> None:
    settings = get_settings()
    admin = _user(
        db,
        email=settings.demo_admin_email,
        password=settings.demo_admin_password,
        full_name="Demo Administrator",
        role="administrator",
        village=None,
    )
    citizen = _user(
        db,
        email=settings.demo_citizen_email,
        password=settings.demo_citizen_password,
        full_name="Demo Citizen",
        role="citizen",
        village="Demo Gram",
    )

    if db.scalar(select(GovernmentScheme.id).limit(1)) is None:
        for item in SCHEMES:
            db.add(
                GovernmentScheme(
                    name=item["name"],
                    short_name=item["short_name"],
                    description=item["description"],
                    eligibility=UNVERIFIED,
                    benefits=UNVERIFIED,
                    required_documents=UNVERIFIED,
                    application_process=UNVERIFIED,
                    official_url=item["official_url"],
                    last_verified_on=None,
                    verification_note="Not verified against an official source in this demo build.",
                    category=item["category"],
                    state_applicability=item["state_applicability"],
                    is_demo=True,
                )
            )
        db.commit()

    if db.scalar(select(EmergencyContact.id).limit(1)) is None:
        for item in EMERGENCY_CONTACTS:
            db.add(EmergencyContact(**item, is_informational=True))
        db.commit()

    if db.scalar(select(Complaint).where(Complaint.tracking_id == "SV-DEMO-0001")) is None:
        complaint = Complaint(
            tracking_id="SV-DEMO-0001",
            user_id=citizen.id,
            contact_name=citizen.full_name,
            contact_phone="9000000000",
            category="drinking_water",
            description=(
                "Sample demonstration complaint: the public handpump near the sample school "
                "is marked for the hackathon flow. This was not sent to a government office."
            ),
            village="Demo Gram",
            location_note="Sample location only",
            status="pending",
        )
        db.add(complaint)
        db.commit()
        db.refresh(complaint)
        db.add(
            ComplaintStatusHistory(
                complaint_id=complaint.id,
                old_status=None,
                new_status="pending",
                note="Sample record created for the demonstration.",
                changed_by_id=admin.id,
            )
        )
        db.commit()
