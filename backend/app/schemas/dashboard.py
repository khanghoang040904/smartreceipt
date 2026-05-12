from pydantic import BaseModel


class StatsSummary(BaseModel):
    total_receipts: int
    total_spending: float
    this_month_spending: float
    avg_per_receipt: float
    month_change_percent: float | None = None


class CategorySpending(BaseModel):
    name: str
    value: float
    color: str


class MonthlySpending(BaseModel):
    month: str
    amount: float


class DashboardResponse(BaseModel):
    stats: StatsSummary
    category_spending: list[CategorySpending]
    monthly_spending: list[MonthlySpending]
