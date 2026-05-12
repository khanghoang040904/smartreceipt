from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.schemas.dashboard import DashboardResponse
from app.services.auth_service import get_current_user
from app.services.statistics_service import (
    get_dashboard_stats,
    get_category_spending,
    get_monthly_spending,
)

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


@router.get("", response_model=DashboardResponse)
def get_dashboard(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    stats = get_dashboard_stats(user.id, db)
    categories = get_category_spending(user.id, db)
    monthly = get_monthly_spending(user.id, db)

    return DashboardResponse(
        stats=stats,
        category_spending=categories,
        monthly_spending=monthly,
    )
