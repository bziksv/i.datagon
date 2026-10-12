"""JSON-схемы предложений агента."""

from decimal import Decimal

from pydantic import BaseModel, Field, field_validator, model_validator


class ProposeOrder(BaseModel):
    ticker: str
    side: str
    qty: int = Field(..., ge=1)
    stop: float = Field(..., gt=0)
    entry_price: float | None = Field(default=None, gt=0)
    price_as_of: str | None = None
    lot: int | None = Field(default=None, ge=1)
    execution_mode: str | None = None
    reason: str
    sleeve: str

    @field_validator("ticker")
    @classmethod
    def ticker_ok(cls, value: str) -> str:
        ticker = value.strip().upper()
        if not ticker:
            raise ValueError("ticker")
        return ticker

    @field_validator("side")
    @classmethod
    def side_ok(cls, value: str) -> str:
        side = value.strip().lower()
        if side not in {"buy", "sell"}:
            raise ValueError("side")
        return side

    @field_validator("reason", "sleeve")
    @classmethod
    def text_ok(cls, value: str) -> str:
        text = value.strip()
        if not text:
            raise ValueError("empty")
        return text


class SleeveWeight(BaseModel):
    sleeve: str
    weight: float = Field(..., ge=0, le=1)

    @field_validator("sleeve")
    @classmethod
    def sleeve_ok(cls, value: str) -> str:
        sleeve = value.strip()
        if not sleeve:
            raise ValueError("sleeve")
        return sleeve


class ProposeWeights(BaseModel):
    weights: list[SleeveWeight] = Field(..., min_length=1)

    @model_validator(mode="after")
    def weights_sum_to_one(self) -> "ProposeWeights":
        total = sum((Decimal(str(row.weight)) for row in self.weights), Decimal("0"))
        if total != Decimal("1"):
            raise ValueError("weights must sum to 1")
        return self
