from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str
    receipt_ids: list[int] | None = None
    date_from: str | None = None
    date_to: str | None = None
    category_id: int | None = None


class ChatSource(BaseModel):
    receipt_id: int
    supplier_name: str | None
    receipt_date: str | None
    total_amount: float
    image_url: str
    chunk_text: str
    score: float


class ChatResponse(BaseModel):
    answer: str
    route: str
    sources: list[ChatSource] = []
    sql_result: dict | None = None
    confidence: float = 0.0
