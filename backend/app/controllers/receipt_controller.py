import os
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.config import UPLOAD_DIR, MAX_FILE_SIZE
from app.models.user import User
from app.models.receipt import Receipt, ReceiptItem
from app.models.category import Category
from app.schemas.receipt import ReceiptResponse, ReceiptUpdate, ReceiptItemResponse
from app.services.auth_service import get_current_user
from app.services.ocr_service import extract_text, parse_receipt
from app.services.receipt_index_service import receipt_index_service

router = APIRouter(prefix="/api/receipts", tags=["Receipts"])


def receipt_to_response(receipt: Receipt) -> ReceiptResponse:
    return ReceiptResponse(
        id=receipt.id,
        image_path=receipt.image_path,
        raw_text=receipt.raw_text,
        supplier_name=receipt.supplier_name,
        receipt_date=receipt.receipt_date,
        total_amount=receipt.total_amount,
        category_id=receipt.category_id,
        category_name=receipt.category.name if receipt.category else None,
        status=receipt.status,
        created_at=receipt.created_at.isoformat(),
        items=[
            ReceiptItemResponse(
                id=item.id,
                item_name=item.item_name,
                quantity=item.quantity,
                unit_price=item.unit_price,
                amount=item.amount,
            )
            for item in receipt.items
        ],
    )


@router.post("/upload", response_model=ReceiptResponse)
async def upload_receipt(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if file.content_type not in ["image/jpeg", "image/png"]:
        raise HTTPException(status_code=400, detail="Only JPG and PNG images are supported")

    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large (max 10MB)")

    ext = os.path.splitext(file.filename or "image.jpg")[1]
    filename = f"{uuid.uuid4().hex}{ext}"
    filepath = os.path.join(UPLOAD_DIR, filename)

    with open(filepath, "wb") as f:
        f.write(contents)

    raw_text = extract_text(filepath)
    parsed = parse_receipt(raw_text)

    receipt = Receipt(
        user_id=user.id,
        image_path=filename,
        raw_text=parsed["raw_text"],
        supplier_name=parsed["supplier_name"],
        receipt_date=parsed["receipt_date"],
        total_amount=parsed["total_amount"],
        status="Chờ duyệt",
    )
    db.add(receipt)
    db.commit()
    db.refresh(receipt)

    for item_data in parsed["items"]:
        item = ReceiptItem(
            receipt_id=receipt.id,
            item_name=item_data["item_name"],
            quantity=item_data["quantity"],
            unit_price=item_data["unit_price"],
            amount=item_data["amount"],
        )
        db.add(item)
    db.commit()
    db.refresh(receipt)
    receipt_index_service.upsert_receipt(receipt)

    return receipt_to_response(receipt)


@router.get("", response_model=list[ReceiptResponse])
def list_receipts(
    search: str | None = Query(None),
    category_id: int | None = Query(None),
    date_from: str | None = Query(None),
    date_to: str | None = Query(None),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(Receipt).filter(Receipt.user_id == user.id)

    if search:
        query = query.filter(Receipt.supplier_name.ilike(f"%{search}%"))
    if category_id:
        query = query.filter(Receipt.category_id == category_id)
    if date_from:
        query = query.filter(Receipt.created_at >= datetime.fromisoformat(date_from))
    if date_to:
        query = query.filter(Receipt.created_at <= datetime.fromisoformat(date_to + "T23:59:59"))

    receipts = query.order_by(Receipt.created_at.desc()).all()
    return [receipt_to_response(r) for r in receipts]


@router.get("/{receipt_id}", response_model=ReceiptResponse)
def get_receipt(
    receipt_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    receipt = db.query(Receipt).filter(Receipt.id == receipt_id, Receipt.user_id == user.id).first()
    if not receipt:
        raise HTTPException(status_code=404, detail="Receipt not found")
    return receipt_to_response(receipt)


@router.put("/{receipt_id}", response_model=ReceiptResponse)
def update_receipt(
    receipt_id: int,
    data: ReceiptUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    receipt = db.query(Receipt).filter(Receipt.id == receipt_id, Receipt.user_id == user.id).first()
    if not receipt:
        raise HTTPException(status_code=404, detail="Receipt not found")

    if data.supplier_name is not None:
        receipt.supplier_name = data.supplier_name
    if data.receipt_date is not None:
        receipt.receipt_date = data.receipt_date
    if data.total_amount is not None:
        receipt.total_amount = data.total_amount
    if data.category_id is not None:
        category = db.query(Category).filter(
            Category.id == data.category_id,
            Category.user_id == user.id,
        ).first()
        if not category:
            raise HTTPException(status_code=400, detail="Category not found")
        receipt.category_id = data.category_id
    if data.status is not None:
        receipt.status = data.status

    if data.items is not None:
        db.query(ReceiptItem).filter(ReceiptItem.receipt_id == receipt.id).delete()
        for item_data in data.items:
            item = ReceiptItem(
                receipt_id=receipt.id,
                item_name=item_data.item_name,
                quantity=item_data.quantity,
                unit_price=item_data.unit_price,
                amount=item_data.amount,
            )
            db.add(item)

    receipt.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(receipt)
    receipt_index_service.upsert_receipt(receipt)
    return receipt_to_response(receipt)


@router.delete("/{receipt_id}")
def delete_receipt(
    receipt_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    receipt = db.query(Receipt).filter(Receipt.id == receipt_id, Receipt.user_id == user.id).first()
    if not receipt:
        raise HTTPException(status_code=404, detail="Receipt not found")

    image_path = os.path.join(UPLOAD_DIR, receipt.image_path)
    if os.path.exists(image_path):
        os.remove(image_path)

    receipt_index_service.delete_receipt(user.id, receipt.id)
    db.delete(receipt)
    db.commit()
    return {"message": "Receipt deleted"}
