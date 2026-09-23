from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.dashboard import DashboardOut, ProjectionOut
from app.services import dashboard_service

router = APIRouter()


@router.get("", response_model=DashboardOut)
def get_dashboard(
    period: str = Query(default="6m", pattern="^(3m|6m|12m|current_year)$"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return dashboard_service.get_dashboard(db, current_user.id, period)


@router.get("/projection", response_model=ProjectionOut)
def get_projection(
    horizon_days: int = Query(default=30, ge=1, le=730),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return dashboard_service.get_projection(db, current_user.id, horizon_days)
