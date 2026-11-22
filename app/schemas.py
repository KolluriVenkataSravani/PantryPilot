from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ItemCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    category: str = Field(default="Other", min_length=1, max_length=60)
    quantity: float = Field(gt=0)
    unit: str = Field(default="item", min_length=1, max_length=30)
    expires_on: date | None = None
    notes: str = Field(default="", max_length=1000)

    @field_validator("name", "category", "unit")
    @classmethod
    def strip_required_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("This field cannot be blank")
        return value


class ItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    category: str
    quantity: float
    unit: str
    expires_on: date | None
    notes: str
    created_at: datetime


class PantrySummary(BaseModel):
    total_items: int
    expiring_soon: int
    expired: int
