import os
import json
from decimal import Decimal
from datetime import date
from typing import Optional

from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.database import get_db, engine, Base
from app.models import Expense

Base.metadata.create_all(bind=engine)

def get_cors_origins():
    origins = [
        "http://localhost:5173",
        "http://localhost:3000",
    ]
    frontend_url = os.getenv("FRONTEND_URL")
    if frontend_url:
        origins.append(frontend_url)
    return origins


middleware = [
    Middleware(
        CORSMiddleware,
        allow_origins=get_cors_origins(),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
]


def serialize_expense(e):
    return {
        "id": e.id,
        "client_id": e.client_id,
        "amount": str(e.amount),
        "category": e.category,
        "description": e.description,
        "date": str(e.date),
        "created_at": e.created_at.isoformat() if e.created_at else None,
    }


async def create_expense(request):
    """Create a new expense."""
    data = await request.json()

    client_id = data.get("client_id", "")
    amount = data.get("amount")
    category = data.get("category", "")
    description = data.get("description")
    date_str = data.get("date", "")

    if not client_id or len(client_id) != 36:
        return JSONResponse({"detail": "client_id must be 36 characters"}, status_code=400)
    if not category:
        return JSONResponse({"detail": "category is required"}, status_code=400)
    if not amount:
        return JSONResponse({"detail": "amount is required"}, status_code=400)
    if not date_str:
        return JSONResponse({"detail": "date is required"}, status_code=400)

    db = next(get_db())
    try:
        existing = db.query(Expense).filter(Expense.client_id == client_id).first()
        if existing:
            return JSONResponse(serialize_expense(existing))

        try:
            amount_decimal = Decimal(str(amount))
            if amount_decimal <= 0:
                return JSONResponse({"detail": "amount must be greater than 0"}, status_code=400)
        except:
            return JSONResponse({"detail": "invalid amount"}, status_code=400)

        try:
            expense_date = date.fromisoformat(date_str)
        except:
            return JSONResponse({"detail": "invalid date format"}, status_code=400)

        db_expense = Expense(
            client_id=client_id,
            amount=amount_decimal,
            category=category,
            description=description,
            date=expense_date,
        )
        db.add(db_expense)
        db.commit()
        db.refresh(db_expense)

        return JSONResponse(serialize_expense(db_expense), status_code=201)
    finally:
        db.close()


async def list_expenses(request):
    """List all expenses."""
    category = request.query_params.get("category")
    sort_param = request.query_params.get("sort")

    db = next(get_db())
    try:
        query = db.query(Expense)

        if category:
            query = query.filter(Expense.category == category)

        if sort_param == "date_desc":
            query = query.order_by(Expense.date.desc())
        else:
            query = query.order_by(Expense.date.asc())

        expenses = query.all()
        total = sum(Decimal(str(e.amount)) for e in expenses)

        return JSONResponse({
            "expenses": [serialize_expense(e) for e in expenses],
            "total": str(total),
        })
    finally:
        db.close()


async def get_categories(request):
    """Get all unique categories."""
    db = next(get_db())
    try:
        categories = db.query(Expense.category).distinct().all()
        return JSONResponse({"categories": [c[0] for c in categories]})
    finally:
        db.close()


async def home(request):
    """Root endpoint."""
    return JSONResponse({
        "message": "Expense Tracker API",
        "endpoints": {
            "POST /expenses": "Create a new expense",
            "GET /expenses": "List all expenses",
            "GET /categories": "Get all unique categories"
        }
    })


routes = [
    Route("/", home),
    Route("/expenses", create_expense, methods=["POST"]),
    Route("/expenses", list_expenses, methods=["GET"]),
    Route("/categories", get_categories, methods=["GET"]),
]

app = Starlette(debug=True, routes=routes, middleware=middleware)
