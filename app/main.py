import os
from fastapi import FastAPI, Depends, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from decimal import Decimal
from typing import Optional

from app.database import get_db, engine, Base
from app.models import Expense
from app.schemas import ExpenseCreate, ExpenseResponse, ExpenseListResponse

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Expense Tracker API", version="1.0.0")

# CORS - allow Vercel frontend and local development
origins = [
    "http://localhost:5173",
    "http://localhost:3000",
    "https://*.vercel.app",  # Allow all Vercel deployments
]

# Add specific Vercel URL if provided via env
if os.getenv("FRONTEND_URL"):
    origins.append(os.getenv("FRONTEND_URL"))

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/expenses", response_model=ExpenseResponse)
def create_expense(expense: ExpenseCreate, db: Session = Depends(get_db)):
    """Create a new expense. Idempotent - returns existing if client_id already exists."""
    # Check if expense with this client_id already exists
    existing = db.query(Expense).filter(Expense.client_id == expense.client_id).first()
    if existing:
        return ExpenseResponse(
            id=existing.id,
            client_id=existing.client_id,
            amount=str(existing.amount),
            category=existing.category,
            description=existing.description,
            date=existing.date,
            created_at=existing.created_at,
        )

    db_expense = Expense(
        client_id=expense.client_id,
        amount=expense.amount,
        category=expense.category,
        description=expense.description,
        date=expense.date,
    )
    db.add(db_expense)
    db.commit()
    db.refresh(db_expense)

    return ExpenseResponse(
        id=db_expense.id,
        client_id=db_expense.client_id,
        amount=str(db_expense.amount),
        category=db_expense.category,
        description=db_expense.description,
        date=db_expense.date,
        created_at=db_expense.created_at,
    )


@app.get("/expenses", response_model=ExpenseListResponse)
def list_expenses(
    category: Optional[str] = Query(None, description="Filter by category"),
    sort: Optional[str] = Query(None, description="Use 'date_desc' for newest first"),
    db: Session = Depends(get_db),
):
    """List expenses with optional category filter and sorting."""
    query = db.query(Expense)

    if category:
        query = query.filter(Expense.category == category)

    if sort == "date_desc":
        query = query.order_by(Expense.date.desc())
    else:
        query = query.order_by(Expense.date.asc())

    expenses = query.all()
    total = sum(Decimal(str(e.amount)) for e in expenses)

    return ExpenseListResponse(
        expenses=[
            ExpenseResponse(
                id=e.id,
                client_id=e.client_id,
                amount=str(e.amount),
                category=e.category,
                description=e.description,
                date=e.date,
                created_at=e.created_at,
            )
            for e in expenses
        ],
        total=str(total),
    )


@app.get("/categories")
def get_categories(db: Session = Depends(get_db)):
    """Get all unique categories."""
    categories = db.query(Expense.category).distinct().all()
    return {"categories": [c[0] for c in categories]}