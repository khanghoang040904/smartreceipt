from __future__ import annotations

import re
from datetime import datetime

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.receipt import Receipt, ReceiptItem
from app.schemas.chat import ChatRequest, ChatResponse, ChatSource
from app.services.receipt_index_service import normalize_for_search, receipt_index_service


AGGREGATE_TERMS = {
    "tong",
    "total",
    "bao nhieu",
    "chi bao nhieu",
    "tieu bao nhieu",
    "cao nhat",
    "lon nhat",
    "max",
    "thap nhat",
    "nho nhat",
    "trung binh",
    "average",
    "bao nhieu hoa don",
}

ITEM_LOOKUP_PHRASES = {
    "tim",
    "tim hoa don",
    "hoa don nao co",
    "hoa don co",
    "lien quan",
    "vat pham",
    "mon",
}

MATCH_STOP_TERMS = {
    "tong",
    "total",
    "tien",
    "hoa",
    "don",
    "bao",
    "nhieu",
    "chi",
    "tieu",
    "ngay",
    "thang",
    "nam",
    "cua",
    "la",
}

ITEM_QUERY_TERMS = {
    "gia",
    "don gia",
    "san pham",
    "mat hang",
    "vat pham",
    "mua",
    "tim",
    "thuoc",
    "hop",
    "chai",
    "goi",
    "kg",
    "ly",
    "suat",
}

ITEM_STOP_TERMS = MATCH_STOP_TERMS | {
    "gia",
    "don",
    "san",
    "pham",
    "mat",
    "hang",
    "vat",
    "mua",
    "tim",
    "lien",
    "quan",
    "den",
    "ve",
    "nhu",
    "bat",
    "ki",
    "ky",
    "cac",
    "mot",
    "1",
    "gi",
    "nao",
    "co",
    "may",
    "hop",
    "chai",
    "goi",
    "kg",
    "ly",
    "suat",
}


def answer_chat(request: ChatRequest, user_id: int, db: Session) -> ChatResponse:
    message = request.message.strip()
    if not message:
        return ChatResponse(answer="Hãy nhập câu hỏi về hóa đơn.", route="empty")

    item_response = _answer_item_question(request, user_id, db)
    if item_response is not None:
        return item_response

    route = _choose_route(message)
    if route == "sql":
        return _answer_sql(request, user_id, db)
    return _answer_hybrid(request, user_id, db)


def reindex_user_receipts(user_id: int, db: Session) -> int:
    receipts = db.query(Receipt).filter(Receipt.user_id == user_id).all()
    for receipt in receipts:
        receipt_index_service.upsert_receipt(receipt)
    return len(receipts)


def _choose_route(message: str) -> str:
    normalized = normalize_for_search(message)
    if any(term in normalized for term in AGGREGATE_TERMS):
        return "sql"
    return "hybrid"


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


def _answer_sql(request: ChatRequest, user_id: int, db: Session) -> ChatResponse:
    normalized = normalize_for_search(request.message)
    base_query = _base_receipt_query(request, user_id, db)
    filtered_query = _apply_month_filter(base_query, normalized)

    matched_receipt = _find_best_receipt_match(filtered_query.all(), request.message)
    if matched_receipt and any(term in normalized for term in ["tong", "total", "bao nhieu"]):
        source = _source_from_receipt(matched_receipt, _receipt_summary(matched_receipt), 1.0)
        return ChatResponse(
            answer=(
                f"Hóa đơn {matched_receipt.supplier_name or matched_receipt.id} "
                f"có tổng tiền {_format_vnd(matched_receipt.total_amount)}."
            ),
            route="sql",
            sources=[source],
            sql_result={
                "operation": "receipt_total",
                "receipt_id": matched_receipt.id,
                "total_amount": matched_receipt.total_amount,
            },
            confidence=0.95,
        )

    if any(term in normalized for term in ["cao nhat", "lon nhat", "max"]):
        receipt = filtered_query.order_by(Receipt.total_amount.desc()).first()
        if not receipt:
            return _empty_response("sql")
        return ChatResponse(
            answer=(
                f"Hóa đơn cao nhất là {receipt.supplier_name or receipt.id} "
                f"với {_format_vnd(receipt.total_amount)}."
            ),
            route="sql",
            sources=[_source_from_receipt(receipt, _receipt_summary(receipt), 1.0)],
            sql_result={"operation": "max_receipt", "receipt_id": receipt.id, "total_amount": receipt.total_amount},
            confidence=0.95,
        )

    if any(term in normalized for term in ["thap nhat", "nho nhat"]):
        receipt = filtered_query.order_by(Receipt.total_amount.asc()).first()
        if not receipt:
            return _empty_response("sql")
        return ChatResponse(
            answer=(
                f"Hóa đơn thấp nhất là {receipt.supplier_name or receipt.id} "
                f"với {_format_vnd(receipt.total_amount)}."
            ),
            route="sql",
            sources=[_source_from_receipt(receipt, _receipt_summary(receipt), 1.0)],
            sql_result={"operation": "min_receipt", "receipt_id": receipt.id, "total_amount": receipt.total_amount},
            confidence=0.95,
        )

    if "trung binh" in normalized or "average" in normalized:
        average = filtered_query.with_entities(func.avg(Receipt.total_amount)).scalar() or 0.0
        count = filtered_query.with_entities(func.count(Receipt.id)).scalar() or 0
        return ChatResponse(
            answer=f"Giá trị trung bình mỗi hóa đơn là {_format_vnd(average)} trên {count} hóa đơn.",
            route="sql",
            sources=_sources_from_receipts(filtered_query.order_by(Receipt.created_at.desc()).limit(3).all()),
            sql_result={"operation": "average", "average_amount": float(average), "count": int(count)},
            confidence=0.9,
        )

    total = filtered_query.with_entities(func.sum(Receipt.total_amount)).scalar() or 0.0
    count = filtered_query.with_entities(func.count(Receipt.id)).scalar() or 0
    return ChatResponse(
        answer=f"Tổng chi tiêu là {_format_vnd(total)} từ {count} hóa đơn.",
        route="sql",
        sources=_sources_from_receipts(filtered_query.order_by(Receipt.created_at.desc()).limit(5).all()),
        sql_result={"operation": "sum", "total_amount": float(total), "count": int(count)},
        confidence=0.9 if count else 0.3,
    )


def _answer_hybrid(request: ChatRequest, user_id: int, db: Session) -> ChatResponse:
    search_results = receipt_index_service.search(
        db=db,
        user_id=user_id,
        query=request.message,
        receipt_ids=request.receipt_ids,
        category_id=request.category_id,
        limit=6,
    )
    if not search_results:
        return _empty_response("hybrid")

    receipt_ids = [result.receipt_id for result in search_results]
    receipts = {
        receipt.id: receipt
        for receipt in db.query(Receipt).filter(Receipt.user_id == user_id, Receipt.id.in_(receipt_ids)).all()
    }
    sources = []
    for result in search_results:
        receipt = receipts.get(result.receipt_id)
        if receipt:
            sources.append(_source_from_receipt(receipt, result.chunk_text, result.score))

    if not sources:
        return _empty_response("hybrid")

    top = sources[0]
    answer = (
        f"Tìm thấy {len(sources)} hóa đơn liên quan. Kết quả phù hợp nhất là "
        f"{top.supplier_name or f'hóa đơn #{top.receipt_id}'} ngày {top.receipt_date or 'không rõ ngày'}, "
        f"tổng tiền {_format_vnd(top.total_amount)}."
    )
    return ChatResponse(
        answer=answer,
        route="hybrid",
        sources=sources,
        confidence=max(source.score for source in sources),
    )


def _answer_item_question(request: ChatRequest, user_id: int, db: Session) -> ChatResponse | None:
    normalized = normalize_for_search(request.message)
    item_intent = _has_item_intent(normalized)
    base_query = _apply_month_filter(_base_receipt_query(request, user_id, db), normalized)
    receipts = base_query.all()
    if not receipts:
        return _empty_item_response() if item_intent else None

    receipt_by_id = {receipt.id: receipt for receipt in receipts}
    rows = (
        db.query(ReceiptItem)
        .filter(ReceiptItem.receipt_id.in_(receipt_by_id.keys()))
        .all()
    )
    if not rows:
        return _answer_item_from_raw_text(receipts, normalized, _meaningful_item_terms(normalized)) if item_intent else None

    terms = _meaningful_item_terms(normalized)
    ranked: list[tuple[float, ReceiptItem, Receipt]] = []
    for item in rows:
        receipt = receipt_by_id.get(item.receipt_id)
        if not receipt:
            continue
        score = _score_item_match(item, receipt, normalized, terms)
        if score > 0:
            ranked.append((score, item, receipt))

    ranked.sort(key=lambda row: row[0], reverse=True)
    top_score = ranked[0][0] if ranked else 0.0
    if ranked and (item_intent or top_score >= 0.75) and top_score >= 0.5:
        return _format_item_response(ranked[:5], normalized)

    if _has_general_purchase_intent(normalized):
        supplier_matches = _receipts_matching_terms(receipts, terms)
        if supplier_matches:
            supplier_ids = {receipt.id for receipt in supplier_matches}
            matched_rows = [
                (1.0, item, receipt_by_id[item.receipt_id])
                for item in rows
                if item.receipt_id in supplier_ids
            ]
            if matched_rows:
                return _format_item_response(matched_rows[:8], normalized, list_all=True)
        return _empty_response("item")

    if item_intent:
        raw_response = _answer_item_from_raw_text(receipts, normalized, terms)
        if raw_response:
            return raw_response
        return _empty_item_response()

    return None


def _has_item_intent(normalized: str) -> bool:
    if any(term in normalized for term in ITEM_QUERY_TERMS):
        return True
    return any(phrase in normalized for phrase in ITEM_LOOKUP_PHRASES)


def _has_general_purchase_intent(normalized: str) -> bool:
    return "mua" in normalized or "san pham" in normalized or "mat hang" in normalized


def _meaningful_item_terms(normalized: str) -> list[str]:
    return [
        term
        for term in normalized.split()
        if len(term) >= 2 and term not in ITEM_STOP_TERMS
    ]


def _score_item_match(
    item: ReceiptItem,
    receipt: Receipt,
    normalized_message: str,
    terms: list[str],
) -> float:
    item_text = normalize_for_search(item.item_name)
    if not item_text:
        return 0.0

    score = 0.0
    if item_text and item_text in normalized_message:
        score += 2.0
    if normalized_message and normalized_message in item_text:
        score += 1.5

    item_terms = set(item_text.split())
    if terms:
        matched = sum(1 for term in terms if term in item_terms or term in item_text)
        score += matched / len(terms)

    supplier = normalize_for_search(receipt.supplier_name)
    if supplier and supplier in normalized_message and score > 0:
        score += 0.35
    return score


def _receipts_matching_terms(receipts: list[Receipt], terms: list[str]) -> list[Receipt]:
    if not terms:
        return receipts
    matches = []
    for receipt in receipts:
        haystack = normalize_for_search("\n".join([receipt.supplier_name or "", receipt.raw_text or ""]))
        if any(term in haystack for term in terms):
            matches.append(receipt)
    return matches


def _format_item_response(
    ranked: list[tuple[float, ReceiptItem, Receipt]],
    normalized_message: str,
    list_all: bool = False,
) -> ChatResponse:
    unique: list[tuple[float, ReceiptItem, Receipt]] = []
    seen: set[int] = set()
    for score, item, receipt in ranked:
        if item.id in seen:
            continue
        seen.add(item.id)
        unique.append((score, item, receipt))

    sources = []
    best_by_receipt: dict[int, tuple[float, ReceiptItem, Receipt]] = {}
    for score, item, receipt in unique:
        current = best_by_receipt.get(receipt.id)
        if current is None or score > current[0]:
            best_by_receipt[receipt.id] = (score, item, receipt)
    for score, item, receipt in sorted(best_by_receipt.values(), key=lambda row: row[0], reverse=True)[:5]:
        sources.append(_source_from_receipt(receipt, _item_summary(item, receipt), min(score, 1.0)))
    if not unique:
        return _empty_response("item")

    if len(unique) == 1 and not list_all:
        _, item, receipt = unique[0]
        answer = (
            f"{item.item_name} trong hóa đơn {receipt.supplier_name or receipt.id} "
            f"có đơn giá {_format_vnd(item.unit_price)}, số lượng {item.quantity}, "
            f"thành tiền {_format_vnd(item.amount)}."
        )
    else:
        parts = [
            (
                f"{item.item_name} x{item.quantity}: đơn giá {_format_vnd(item.unit_price)}, "
                f"thành tiền {_format_vnd(item.amount)} ({receipt.supplier_name or receipt.id})"
            )
            for _, item, receipt in unique[:6]
        ]
        answer = "Tìm thấy các sản phẩm phù hợp: " + "; ".join(parts) + "."

    return ChatResponse(
        answer=answer,
        route="item",
        sources=sources,
        sql_result={
            "operation": "item_lookup",
            "items": [
                {
                    "receipt_id": receipt.id,
                    "item_id": item.id,
                    "item_name": item.item_name,
                    "quantity": item.quantity,
                    "unit_price": item.unit_price,
                    "amount": item.amount,
                }
                for _, item, receipt in unique[:6]
            ],
            "intent": "price" if "gia" in normalized_message or "don gia" in normalized_message else "items",
        },
        confidence=max(min(score, 1.0) for score, _, _ in unique),
    )


def _item_summary(item: ReceiptItem, receipt: Receipt) -> str:
    return "\n".join([
        f"Nhà cung cấp: {receipt.supplier_name or 'Không rõ'}",
        f"Ngày: {receipt.receipt_date or 'Không rõ'}",
        f"Sản phẩm: {item.item_name}",
        f"Số lượng: {item.quantity}",
        f"Đơn giá: {_format_vnd(item.unit_price)}",
        f"Thành tiền: {_format_vnd(item.amount)}",
    ])


def _format_vnd(value: float) -> str:
    return f"{value:,.0f}".replace(",", ".") + " đ"


def _answer_item_from_raw_text(
    receipts: list[Receipt],
    normalized_message: str,
    terms: list[str],
) -> ChatResponse | None:
    if not terms:
        return _empty_item_response()
    scored = []
    for receipt in receipts:
        haystack = normalize_for_search("\n".join([receipt.supplier_name or "", receipt.raw_text or ""]))
        matched = sum(1 for term in terms if term in haystack)
        if matched == 0:
            continue
        score = matched / len(terms)
        if score >= 0.75 or (len(terms) <= 2 and score >= 0.5):
            scored.append((score, receipt))
    if not scored:
        return _empty_item_response()
    scored.sort(key=lambda row: row[0], reverse=True)
    sources = [
        _source_from_receipt(receipt, _receipt_summary(receipt), min(score, 1.0))
        for score, receipt in scored[:5]
    ]
    names = ", ".join(source.supplier_name or f"hóa đơn #{source.receipt_id}" for source in sources)
    return ChatResponse(
        answer=f"Tìm thấy {len(sources)} hóa đơn có dữ liệu liên quan đến vật phẩm này: {names}.",
        route="item_raw",
        sources=sources,
        sql_result={"operation": "item_raw_lookup", "matched_terms": terms},
        confidence=max(source.score for source in sources),
    )


def _find_best_receipt_match(receipts: list[Receipt], message: str) -> Receipt | None:
    normalized_message = normalize_for_search(message)
    best_receipt = None
    best_score = 0.0
    for receipt in receipts:
        haystack = normalize_for_search(
            "\n".join([
                receipt.supplier_name or "",
                receipt.raw_text or "",
                str(receipt.total_amount or ""),
            ])
        )
        supplier = normalize_for_search(receipt.supplier_name)
        score = 0.0
        if supplier and supplier in normalized_message:
            score += 3.0
        terms = [
            term
            for term in normalized_message.split()
            if len(term) >= 3 and term not in MATCH_STOP_TERMS
        ]
        if terms:
            score += sum(1 for term in terms if term in haystack) / len(terms)
        if score > best_score:
            best_receipt = receipt
            best_score = score
    return best_receipt if best_score >= 0.35 else None


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


def _sources_from_receipts(receipts: list[Receipt]) -> list[ChatSource]:
    return [_source_from_receipt(receipt, _receipt_summary(receipt), 1.0) for receipt in receipts]


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
        f"Tổng tiền: {_format_vnd(receipt.total_amount)}",
        receipt.raw_text or "",
    ]).strip()


def _empty_response(route: str) -> ChatResponse:
    return ChatResponse(
        answer="Không đủ dữ liệu trong các hóa đơn đã lưu để trả lời câu hỏi này.",
        route=route,
        sources=[],
        confidence=0.0,
    )


def _empty_item_response() -> ChatResponse:
    return ChatResponse(
        answer="Không tìm thấy hóa đơn có vật phẩm này trong dữ liệu đã lưu.",
        route="item",
        sources=[],
        sql_result={"operation": "item_lookup", "items": []},
        confidence=0.0,
    )
