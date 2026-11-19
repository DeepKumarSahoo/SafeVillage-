from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.data.demo_content import SCHEME_NOTICE
from app.database import get_db
from app.models import GovernmentScheme
from app.schemas import SchemeListResponse, SchemeResponse
from app.services.locations import validate_query

router = APIRouter(prefix="/api/schemes", tags=["Government schemes"])


@router.get("/categories")
def categories(db: Session = Depends(get_db)) -> dict:
    rows = db.scalars(select(GovernmentScheme.category).distinct().order_by(GovernmentScheme.category)).all()
    return {"categories": rows, "notice": SCHEME_NOTICE}


@router.get("/search", response_model=SchemeListResponse)
def search(q: str = Query(min_length=1, max_length=80), db: Session = Depends(get_db)) -> SchemeListResponse:
    query = validate_query(q, required=True)
    like = f"%{query}%"
    rows = db.scalars(
        select(GovernmentScheme)
        .where(
            or_(
                GovernmentScheme.name.ilike(like),
                GovernmentScheme.short_name.ilike(like),
                GovernmentScheme.category.ilike(like),
                GovernmentScheme.description.ilike(like),
            )
        )
        .order_by(GovernmentScheme.short_name)
    ).all()
    return SchemeListResponse(notice=SCHEME_NOTICE, schemes=rows)


@router.get("", response_model=SchemeListResponse)
def list_schemes(
    category: str | None = Query(default=None, max_length=60),
    state: str | None = Query(default=None, max_length=120),
    db: Session = Depends(get_db),
) -> SchemeListResponse:
    statement = select(GovernmentScheme)
    if category:
        statement = statement.where(GovernmentScheme.category == category.strip().lower())
    if state:
        statement = statement.where(GovernmentScheme.state_applicability.ilike(f"%{state.strip()}%"))
    rows = db.scalars(statement.order_by(GovernmentScheme.short_name)).all()
    return SchemeListResponse(notice=SCHEME_NOTICE, schemes=rows)


@router.get("/{scheme_id}", response_model=SchemeResponse)
def get_scheme(scheme_id: int, db: Session = Depends(get_db)) -> GovernmentScheme:
    scheme = db.get(GovernmentScheme, scheme_id)
    if scheme is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scheme not found.")
    return scheme
