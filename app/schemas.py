from pydantic import BaseModel, Field
from decimal import Decimal
from datetime import date, datetime
from typing import Optional, List


class ExpenseCreate(BaseModel):
    client_id: str = Field(..., min_length=36, max_length=36)
    amount: Decimal = Field(..., gt=0)
    category: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    date: date


class ExpenseResponse(BaseModel):
    id: int
    client_id: str
    amount: str
    category: str
    description: Optional[str]
    date: date
    created_at: datetime

    class Config:
        orm_mode = True


class ExpenseListResponse(BaseModel):
    expenses: List[ExpenseResponse]
    total: str
