from pydantic import BaseModel, Field


class BudgetUpsert(BaseModel):
    category_id: int
    month: str = Field(pattern=r"^\d{4}-\d{2}$")
    amount: float = Field(ge=0)


class BudgetCategorySummary(BaseModel):
    budget_id: int | None = None
    category_id: int
    category_name: str
    month: str
    budget_amount: float
    spent_amount: float
    remaining_amount: float
    usage_percent: float
    status: str


class BudgetSummaryResponse(BaseModel):
    month: str
    total_budget: float
    total_spent: float
    total_remaining: float
    categories: list[BudgetCategorySummary]
