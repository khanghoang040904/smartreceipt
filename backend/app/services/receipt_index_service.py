from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from typing import Any

from sqlalchemy.orm import Session

from app.config import RAG_EMBEDDING_MODEL, VECTORSTORE_DIR
from app.models.receipt import Receipt


@dataclass
class ReceiptChunk:
    id: str
    document: str
    metadata: dict[str, Any]


@dataclass
class ReceiptSearchResult:
    receipt_id: int
    chunk_text: str
    score: float


def normalize_for_search(text: str | None) -> str:
    if not text:
        return ""
    normalized = unicodedata.normalize("NFKD", text)
    normalized = "".join(ch for ch in normalized if not unicodedata.combining(ch))
    normalized = normalized.replace("Đ", "D").replace("đ", "d").lower()
    normalized = re.sub(r"[^a-z0-9]+", " ", normalized)
    return re.sub(r"\s+", " ", normalized).strip()


def build_receipt_chunks(receipt: Receipt) -> list[ReceiptChunk]:
    category_name = receipt.category.name if receipt.category else ""
    item_lines = [
        f"{item.item_name}: số lượng {item.quantity}, đơn giá {item.unit_price:,.0f} đ, thành tiền {item.amount:,.0f} đ"
        for item in receipt.items
    ]
    common_metadata = {
        "user_id": receipt.user_id,
        "receipt_id": receipt.id,
        "receipt_key": f"{receipt.user_id}:{receipt.id}",
        "supplier": receipt.supplier_name or "",
        "date": receipt.receipt_date or "",
        "total": float(receipt.total_amount or 0),
        "category_id": receipt.category_id or 0,
        "category": category_name,
    }
    summary = "\n".join([
        f"Hóa đơn #{receipt.id}",
        f"Nhà cung cấp: {receipt.supplier_name or 'Không rõ'}",
        f"Ngày: {receipt.receipt_date or 'Không rõ'}",
        f"Tổng tiền: {receipt.total_amount or 0:,.0f} đ",
        f"Danh mục: {category_name or 'Chưa phân loại'}",
        f"Trạng thái: {receipt.status}",
    ])
    chunks = [
        ReceiptChunk(
            id=f"{receipt.user_id}:{receipt.id}:summary",
            document=summary,
            metadata={**common_metadata, "chunk_type": "summary"},
        )
    ]

    if item_lines:
        chunks.append(
            ReceiptChunk(
                id=f"{receipt.user_id}:{receipt.id}:items",
                document="Sản phẩm:\n" + "\n".join(item_lines),
                metadata={**common_metadata, "chunk_type": "items"},
            )
        )

    raw_text = receipt.raw_text or ""
    raw_parts = _split_text(raw_text, max_chars=1200)
    for index, part in enumerate(raw_parts):
        chunks.append(
            ReceiptChunk(
                id=f"{receipt.user_id}:{receipt.id}:raw:{index}",
                document=part,
                metadata={**common_metadata, "chunk_type": "raw"},
            )
        )

    return chunks


class LocalEmbeddingFunction:
    def __init__(self, model_name: str = RAG_EMBEDDING_MODEL):
        self.model_name = model_name
        self._model = None

    def _load_model(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(self.model_name)
        return self._model

    def __call__(self, input: list[str]) -> list[list[float]]:
        model = self._load_model()
        embeddings = model.encode(input, normalize_embeddings=True)
        return embeddings.tolist()


class ReceiptIndexService:
    def __init__(self):
        self._collection = None
        self._load_failed = False

    def upsert_receipt(self, receipt: Receipt) -> None:
        collection = self._get_collection()
        if collection is None:
            return
        chunks = build_receipt_chunks(receipt)
        try:
            self.delete_receipt(receipt.user_id, receipt.id)
            if not chunks:
                return
            collection.add(
                ids=[chunk.id for chunk in chunks],
                documents=[chunk.document for chunk in chunks],
                metadatas=[chunk.metadata for chunk in chunks],
            )
        except Exception:
            self._load_failed = True

    def delete_receipt(self, user_id: int, receipt_id: int) -> None:
        collection = self._get_collection()
        if collection is None:
            return
        receipt_key = f"{user_id}:{receipt_id}"
        try:
            existing = collection.get(where={"receipt_key": receipt_key})
            ids = existing.get("ids", []) if existing else []
            if ids:
                collection.delete(ids=ids)
        except Exception:
            self._load_failed = True

    def search(
        self,
        db: Session,
        user_id: int,
        query: str,
        receipt_ids: list[int] | None = None,
        category_id: int | None = None,
        limit: int = 6,
    ) -> list[ReceiptSearchResult]:
        collection = self._get_collection()
        if collection is not None:
            results = self._search_chroma(collection, user_id, query, receipt_ids, category_id, limit)
            if results:
                return results
        return self._search_lexical(db, user_id, query, receipt_ids, category_id, limit)

    def _get_collection(self):
        if self._load_failed:
            return None
        if self._collection is not None:
            return self._collection
        try:
            import chromadb

            client = chromadb.PersistentClient(path=VECTORSTORE_DIR)
            self._collection = client.get_or_create_collection(
                name="receipt_chunks",
                embedding_function=LocalEmbeddingFunction(),
                metadata={"hnsw:space": "cosine"},
            )
            return self._collection
        except Exception:
            self._load_failed = True
            return None

    def _search_chroma(
        self,
        collection,
        user_id: int,
        query: str,
        receipt_ids: list[int] | None,
        category_id: int | None,
        limit: int,
    ) -> list[ReceiptSearchResult]:
        where: dict[str, Any] = {"user_id": user_id}
        if category_id is not None:
            where = {"$and": [where, {"category_id": category_id}]}
        if receipt_ids:
            where = {
                "$and": [
                    where,
                    {"receipt_id": {"$in": receipt_ids}},
                ]
            }
        try:
            response = collection.query(
                query_texts=[query],
                n_results=limit,
                where=where,
                include=["documents", "metadatas", "distances"],
            )
        except Exception:
            return []

        documents = response.get("documents", [[]])[0]
        metadatas = response.get("metadatas", [[]])[0]
        distances = response.get("distances", [[]])[0]
        results = []
        for document, metadata, distance in zip(documents, metadatas, distances):
            score = max(0.0, 1.0 - float(distance or 0))
            results.append(
                ReceiptSearchResult(
                    receipt_id=int(metadata["receipt_id"]),
                    chunk_text=document,
                    score=score,
                )
            )
        return results

    def _search_lexical(
        self,
        db: Session,
        user_id: int,
        query: str,
        receipt_ids: list[int] | None,
        category_id: int | None,
        limit: int,
    ) -> list[ReceiptSearchResult]:
        receipt_query = db.query(Receipt).filter(Receipt.user_id == user_id)
        if receipt_ids:
            receipt_query = receipt_query.filter(Receipt.id.in_(receipt_ids))
        if category_id is not None:
            receipt_query = receipt_query.filter(Receipt.category_id == category_id)

        query_terms = set(normalize_for_search(query).split())
        if not query_terms:
            return []

        ranked = []
        for receipt in receipt_query.all():
            chunks = build_receipt_chunks(receipt)
            combined = "\n\n".join(chunk.document for chunk in chunks)
            haystack = normalize_for_search(combined)
            matched_terms = sum(1 for term in query_terms if term in haystack)
            supplier = normalize_for_search(receipt.supplier_name)
            normalized_query = normalize_for_search(query)
            supplier_bonus = 2 if supplier and supplier in normalized_query else 0
            score = (matched_terms + supplier_bonus) / max(len(query_terms), 1)
            if score > 0:
                ranked.append(ReceiptSearchResult(receipt.id, combined[:1600], min(score, 1.0)))

        ranked.sort(key=lambda item: item.score, reverse=True)
        return ranked[:limit]


def _split_text(text: str, max_chars: int) -> list[str]:
    text = text.strip()
    if not text:
        return []
    parts = []
    current = []
    current_len = 0
    for line in text.splitlines():
        if current and current_len + len(line) + 1 > max_chars:
            parts.append("\n".join(current))
            current = []
            current_len = 0
        current.append(line)
        current_len += len(line) + 1
    if current:
        parts.append("\n".join(current))
    return parts


receipt_index_service = ReceiptIndexService()
