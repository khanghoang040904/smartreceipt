from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.budget import Budget
from app.models.category import Category
from app.models.receipt import Receipt
from app.models.user import User
from app.schemas.budget import BudgetSummaryResponse, BudgetCategorySummary, BudgetUpsert
from app.services.auth_service import get_current_user

router = APIRouter(prefix="/api/budgets", tags=["Budgets"])


@router.get("", response_model=BudgetSummaryResponse)
def get_budgets(
    month: str = Query(..., pattern=r"^\d{4}-\d{2}$"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    categories = db.query(Category).filter(Category.user_id == user.id).order_by(Category.name.asc()).all()
    budgets = {
        budget.category_id: budget
        for budget in db.query(Budget).filter(Budget.user_id == user.id, Budget.month == month).all()
    }
    spent_by_category = _spent_by_category(db, user.id, month)

    summaries = []
    for category in categories:
        budget = budgets.get(category.id)
        budget_amount = float(budget.amount if budget else 0.0)
        spent_amount = float(spent_by_category.get(category.id, 0.0))
        remaining = budget_amount - spent_amount
        usage = (spent_amount / budget_amount * 100) if budget_amount > 0 else 0.0
        summaries.append(
            BudgetCategorySummary(
                budget_id=budget.id if budget else None,
                category_id=category.id,
                category_name=category.name,
                month=month,
                budget_amount=budget_amount,
                spent_amount=spent_amount,
                remaining_amount=remaining,
                usage_percent=round(usage, 2),
                status=_budget_status(usage, budget_amount),
            )
        )

    total_budget = sum(item.budget_amount for item in summaries)
    total_spent = sum(item.spent_amount for item in summaries)
    return BudgetSummaryResponse(
        month=month,
        total_budget=total_budget,
        total_spent=total_spent,
        total_remaining=total_budget - total_spent,
        categories=summaries,
    )


@router.put("", response_model=BudgetCategorySummary)
def upsert_budget(
    data: BudgetUpsert,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    category = db.query(Category).filter(Category.id == data.category_id, Category.user_id == user.id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Không tìm thấy danh mục")

    budget = db.query(Budget).filter(
        Budget.user_id == user.id,
        Budget.category_id == data.category_id,
        Budget.month == data.month,
    ).first()
    if budget:
        budget.amount = data.amount
    else:
        budget = Budget(
            user_id=user.id,
            category_id=data.category_id,
            month=data.month,
            amount=data.amount,
        )
        db.add(budget)

    budget.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(budget)

    spent = _spent_by_category(db, user.id, data.month).get(category.id, 0.0)
    usage = (spent / budget.amount * 100) if budget.amount > 0 else 0.0
    return BudgetCategorySummary(
        budget_id=budget.id,
        category_id=category.id,
        category_name=category.name,
        month=data.month,
        budget_amount=budget.amount,
        spent_amount=spent,
        remaining_amount=budget.amount - spent,
        usage_percent=round(usage, 2),
        status=_budget_status(usage, budget.amount),
    )


@router.delete("/{budget_id}")
def delete_budget(
    budget_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    budget = db.query(Budget).filter(Budget.id == budget_id, Budget.user_id == user.id).first()
    if not budget:
        raise HTTPException(status_code=404, detail="Không tìm thấy ngân sách")
    db.delete(budget)
    db.commit()
    return {"message": "Đã xóa ngân sách"}


def _budget_status(usage_percent: float, budget_amount: float) -> str:
    if budget_amount <= 0:
        return "unset"
    if usage_percent >= 100:
        return "over"
    if usage_percent >= 80:
        return "warning"
    return "ok"


def _spent_by_category(db: Session, user_id: int, month: str) -> dict[int, float]:
    receipts = db.query(Receipt).filter(Receipt.user_id == user_id).all()
    spent: dict[int, float] = {}
    for receipt in receipts:
        if receipt.category_id is None:
            continue
        if _receipt_month(receipt) != month:
            continue
        spent[receipt.category_id] = spent.get(receipt.category_id, 0.0) + float(receipt.total_amount or 0.0)
    return spent


def _receipt_month(receipt: Receipt) -> str:
    parsed = _parse_receipt_date(receipt.receipt_date)
    if not parsed:
        parsed = receipt.created_at
    return parsed.strftime("%Y-%m")


def _parse_receipt_date(value: str | None) -> datetime | None:
    if not value:
        return None
    for fmt in ("%d/%m/%Y", "%d/%m/%y", "%d-%m-%Y", "%d-%m-%y"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    return None
