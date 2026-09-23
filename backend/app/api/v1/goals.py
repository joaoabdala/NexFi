import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.common import MessageResponse
from app.schemas.goal import GoalCreate, GoalOut, GoalUpdate
from app.services import goal_service

router = APIRouter()


@router.get("", response_model=list[GoalOut])
def list_goals(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return goal_service.list_goals(db, current_user.id)


@router.post("", response_model=GoalOut, status_code=201)
def create_goal(
    payload: GoalCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return goal_service.create_goal(db, current_user.id, payload)


@router.put("/{goal_id}", response_model=GoalOut)
def update_goal(
    goal_id: uuid.UUID,
    payload: GoalUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return goal_service.update_goal(db, current_user.id, goal_id, payload)


@router.delete("/{goal_id}", response_model=MessageResponse)
def delete_goal(
    goal_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    goal_service.delete_goal(db, current_user.id, goal_id)
    return MessageResponse(message="Meta removida.")
