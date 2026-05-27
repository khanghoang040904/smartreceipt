from __future__ import annotations

import logging
import re
from datetime import datetime

from sqlalchemy.orm import Session

from app.models.receipt import Receipt
from app.schemas.chat import ChatRequest, ChatResponse, ChatSource
from app.services.gemini_service import chat_with_context
from app.services.receipt_index_service import normalize_for_search, receipt_index_service

logger = logging.getLogger(__name__)


def answer_chat(request: ChatRequest, user_id: int, db: Session) -> ChatResponse:
    message = request.message.strip()
    if not message:
        return ChatResponse(answer="Hãy nhập câu hỏi về hóa đơn.", route="empty")

    return _answer_with_gemini(request, user_id, db)


def reindex_user_receipts(user_id: int, db: Session) -> int:
    receipts = db.query(Receipt).filter(Receipt.user_id == user_id).all()
    for receipt in receipts:
        receipt_index_service.upsert_receipt(receipt)
    return len(receipts)


def _answer_with_gemini(request: ChatRequest, user_id: int, db: Session) -> ChatResponse:
    """RAG + Gemini: retrieve relevant receipts, build context, ask Gemini."""
    base_query = _base_receipt_query(request, user_id, db)
    normalized = normalize_for_search(request.message)
    filtered_query = _apply_month_filter(base_query, normalized)

    search_results = receipt_index_service.search(
        db=db,
        user_id=user_id,
        query=request.message,
        receipt_ids=request.receipt_ids,
        category_id=request.category_id,
        limit=10,
    )

    all_receipts = filtered_query.all()
    search_receipt_ids = {r.receipt_id for r in search_results}
    receipt_map = {r.id: r for r in all_receipts}

    relevant_ids = list(search_receipt_ids | set(receipt_map.keys()))
    if not relevant_ids:
        return _empty_response()

    if search_receipt_ids - set(receipt_map.keys()):
        extra = (
            db.query(Receipt)
            .filter(Receipt.user_id == user_id, Receipt.id.in_(list(search_receipt_ids)))
            .all()
        )
        for r in extra:
            receipt_map[r.id] = r

    context_parts = []
    sources = []
    for result in search_results[:6]:
        receipt = receipt_map.get(result.receipt_id)
        if receipt:
            context_parts.append(_build_receipt_context(receipt))
            sources.append(_source_from_receipt(receipt, result.chunk_text, result.score))

    for receipt in all_receipts:
        if receipt.id not in search_receipt_ids:
            context_parts.append(_build_receipt_context(receipt))
            if len(sources) < 5:
                sources.append(_source_from_receipt(receipt, _receipt_summary(receipt), 0.5))

    receipt_context = "\n\n---\n\n".join(context_parts[:15])

    total_count = len(all_receipts)
    total_sum = sum(r.total_amount or 0 for r in all_receipts)
    summary_line = f"\nTổng cộng: {total_count} hóa đơn, tổng chi tiêu: {total_sum:,.0f} đ."
    receipt_context += "\n" + summary_line

    gemini_answer = chat_with_context(request.message, receipt_context)

    if gemini_answer:
        return ChatResponse(
            answer=gemini_answer,
            route="gemini",
            sources=sources[:5],
            confidence=0.9,
        )

    return _empty_response()


def _build_receipt_context(receipt: Receipt) -> str:
    lines = [
        f"Hóa đơn #{receipt.id}",
        f"Nhà cung cấp: {receipt.supplier_name or 'Không rõ'}",
        f"Ngày: {receipt.receipt_date or 'Không rõ'}",
        f"Tổng tiền: {receipt.total_amount or 0:,.0f} đ",
        f"Trạng thái: {receipt.status}",
    ]
    if receipt.category:
        lines.append(f"Danh mục: {receipt.category.name}")
    if receipt.items:
        lines.append("Sản phẩm:")
        for item in receipt.items:
            lines.append(
                f"  - {item.item_name}: SL {item.quantity}, "
                f"đơn giá {item.unit_price:,.0f} đ, "
                f"thành tiền {item.amount:,.0f} đ"
            )
    return "\n".join(lines)


def _base_receipt_query(request: ChatRequest, user_id: int, db: Session):
    query = db.query(Receipt).filter(Receipt.user_id == user_id)
    if request.receipt_ids:
        query = query.filter(Receipt.id.in_(request.receipt_ids))
    if request.category_id is not None:
        query = query.filter(Receipt.category_id == request.category_id)
    if request.date_from:
        query = query.filter(Receipt.created_at >= datetime.fromisoformat(request.date_from))
    if request.date_to:
        query = query.filter(Receipt.created_at <= datetime.fromisoformat(request.date_to + "T23:59:59"))
    return query


def _apply_month_filter(query, normalized_message: str):
    month_match = re.search(r"thang\s+(\d{1,2})(?:\s+nam\s+(\d{4}))?", normalized_message)
    if not month_match:
        return query
    month = int(month_match.group(1))
    year = int(month_match.group(2)) if month_match.group(2) else None
    receipts = query.all()
    matching_ids = []
    for receipt in receipts:
        parsed = _parse_receipt_date(receipt.receipt_date)
        if not parsed:
            parsed = receipt.created_at
        if parsed.month == month and (year is None or parsed.year == year):
            matching_ids.append(receipt.id)
    if not matching_ids:
        return query.filter(Receipt.id == -1)
    return query.filter(Receipt.id.in_(matching_ids))


def _parse_receipt_date(value: str | None) -> datetime | None:
    if not value:
        return None
    for fmt in ("%d/%m/%Y", "%d/%m/%y", "%d-%m-%Y", "%d-%m-%y"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    return None


def _source_from_receipt(receipt: Receipt, chunk_text: str, score: float) -> ChatSource:
    return ChatSource(
        receipt_id=receipt.id,
        supplier_name=receipt.supplier_name,
        receipt_date=receipt.receipt_date,
        total_amount=receipt.total_amount,
        image_url=f"/uploads/{receipt.image_path}",
        chunk_text=chunk_text,
        score=round(float(score), 3),
    )


def _receipt_summary(receipt: Receipt) -> str:
    return "\n".join([
        f"Nhà cung cấp: {receipt.supplier_name or 'Không rõ'}",
        f"Ngày: {receipt.receipt_date or 'Không rõ'}",
        f"Tổng tiền: {receipt.total_amount or 0:,.0f} đ",
        receipt.raw_text or "",
    ]).strip()


def _empty_response() -> ChatResponse:
    return ChatResponse(
        answer="Không đủ dữ liệu trong các hóa đơn đã lưu để trả lời câu hỏi này.",
        route="gemini",
        sources=[],
        confidence=0.0,
    )
