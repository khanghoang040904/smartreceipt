from datetime import datetime, timedelta

from sqlalchemy import func, extract
from sqlalchemy.orm import Session

from app.models.receipt import Receipt
from app.models.category import Category

CATEGORY_COLORS = {
    "Thực phẩm": "#6366f1",
    "Đồ uống": "#22c55e",
    "Văn phòng phẩm": "#f97316",
    "Khác": "#a855f7",
}


def get_dashboard_stats(user_id: int, db: Session) -> dict:
    now = datetime.utcnow()
    first_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    if now.month == 1:
        first_of_prev_month = first_of_month.replace(year=now.year - 1, month=12)
    else:
        first_of_prev_month = first_of_month.replace(month=now.month - 1)

    total_receipts = db.query(func.count(Receipt.id)).filter(Receipt.user_id == user_id).scalar() or 0
    total_spending = db.query(func.sum(Receipt.total_amount)).filter(Receipt.user_id == user_id).scalar() or 0.0

    this_month = (
        db.query(func.sum(Receipt.total_amount))
        .filter(Receipt.user_id == user_id, Receipt.created_at >= first_of_month)
        .scalar() or 0.0
    )

    prev_month = (
        db.query(func.sum(Receipt.total_amount))
        .filter(
            Receipt.user_id == user_id,
            Receipt.created_at >= first_of_prev_month,
            Receipt.created_at < first_of_month,
        )
        .scalar() or 0.0
    )

    avg_per_receipt = total_spending / total_receipts if total_receipts > 0 else 0.0
    month_change = ((this_month - prev_month) / prev_month * 100) if prev_month > 0 else None

    return {
        "total_receipts": total_receipts,
        "total_spending": total_spending,
        "this_month_spending": this_month,
        "avg_per_receipt": round(avg_per_receipt, 0),
        "month_change_percent": round(month_change, 1) if month_change is not None else None,
    }


def get_category_spending(user_id: int, db: Session) -> list[dict]:
    results = (
        db.query(Category.name, func.sum(Receipt.total_amount))
        .join(Receipt, Receipt.category_id == Category.id)
        .filter(Receipt.user_id == user_id)
        .group_by(Category.name)
        .all()
    )
    return [
        {
            "name": name,
            "value": float(total or 0),
            "color": CATEGORY_COLORS.get(name, "#94a3b8"),
        }
        for name, total in results
    ]


def get_monthly_spending(user_id: int, db: Session) -> list[dict]:
    now = datetime.utcnow()
    months = []
    for i in range(5, -1, -1):
        month = now.month - i
        year = now.year
        while month <= 0:
            month += 12
            year -= 1
        months.append((year, month))

    result = []
    month_names = ["Th1", "Th2", "Th3", "Th4", "Th5", "Th6", "Th7", "Th8", "Th9", "Th10", "Th11", "Th12"]

    for year, month in months:
        total = (
            db.query(func.sum(Receipt.total_amount))
            .filter(
                Receipt.user_id == user_id,
                extract("year", Receipt.created_at) == year,
                extract("month", Receipt.created_at) == month,
            )
            .scalar() or 0.0
        )
        result.append({"month": month_names[month - 1], "amount": float(total)})

    return result
