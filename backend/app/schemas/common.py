from decimal import Decimal
from typing import Annotated, Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class Page(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    page_size: int


class MessageResponse(BaseModel):
    message: str


DecimalStr = Decimal


# Valores monetários de ENTRADA. max_digits/decimal_places espelham a coluna Numeric(15,2): sem
# isso, 1e15 estoura no Postgres (erro 500) e 0,001 vira 0,00 silenciosamente.
Money = Annotated[Decimal, Field(max_digits=15, decimal_places=2)]
PositiveMoney = Annotated[Decimal, Field(gt=0, max_digits=15, decimal_places=2)]
NonNegativeMoney = Annotated[Decimal, Field(ge=0, max_digits=15, decimal_places=2)]
