import uuid

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


class InstitutionCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    short_name: str | None = Field(default=None, max_length=64)
    active: bool = True
    note: str | None = None


class InstitutionUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    short_name: str | None = Field(default=None, max_length=64)
    active: bool | None = None
    note: str | None = None


class InstitutionOut(ORMModel):
    id: uuid.UUID
    name: str
    short_name: str | None
    active: bool
    note: str | None
