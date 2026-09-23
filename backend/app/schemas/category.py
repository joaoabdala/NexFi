import uuid

from pydantic import BaseModel, Field

from app.models.enums import CategoryKind
from app.schemas.common import ORMModel


class CategoryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    kind: CategoryKind
    parent_id: uuid.UUID | None = None
    active: bool = True


class CategoryUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    kind: CategoryKind | None = None
    active: bool | None = None


class CategoryOut(ORMModel):
    id: uuid.UUID
    name: str
    kind: CategoryKind
    parent_id: uuid.UUID | None
    active: bool
    children: list["CategoryOut"] = []
