from pydantic import BaseModel, Field, ConfigDict
from decimal import Decimal
from datetime import date, datetime
from typing import Optional


class ExpenseBase(BaseModel):
    amount: Decimal = Field(..., gt=0, decimal_places=2, description="Amount in INR")
    category: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    date: date


class ExpenseCreate(ExpenseBase):
    client_id: str = Field(..., min_length=36, max_length=36, description="UUID v4 for idempotency")


class ExpenseResponse(ExpenseBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    client_id: str
    amount: str
    created_at: datetime


class ExpenseListResponse(BaseModel):
    expenses: list[ExpenseResponse]
    total: str