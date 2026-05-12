import csv
import io

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.receipt import Receipt
from app.services.auth_service import get_current_user

router = APIRouter(prefix="/api/export", tags=["Export"])


@router.get("/csv")
def export_csv(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    receipts = (
        db.query(Receipt)
        .filter(Receipt.user_id == user.id)
        .order_by(Receipt.created_at.desc())
        .all()
    )

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Date", "Supplier", "Category", "Total Amount", "Status", "Created At"])

    for r in receipts:
        writer.writerow([
            r.id,
            r.receipt_date or "",
            r.supplier_name or "",
            r.category.name if r.category else "",
            r.total_amount,
            r.status,
            r.created_at.isoformat(),
        ])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=receipts_export.csv"},
    )
