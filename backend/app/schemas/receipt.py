from pydantic import BaseModel


class ReceiptItemCreate(BaseModel):
    item_name: str
    quantity: int = 1
    unit_price: float = 0.0
    amount: float = 0.0


class ReceiptItemResponse(BaseModel):
    id: int
    item_name: str
    quantity: int
    unit_price: float
    amount: float

    model_config = {"from_attributes": True}


class ReceiptUpdate(BaseModel):
    supplier_name: str | None = None
    receipt_date: str | None = None
    total_amount: float | None = None
    category_id: int | None = None
    status: str | None = None
    items: list[ReceiptItemCreate] | None = None


class ReceiptResponse(BaseModel):
    id: int
    image_path: str
    raw_text: str | None
    supplier_name: str | None
    receipt_date: str | None
    total_amount: float
    category_id: int | None
    category_name: str | None = None
    status: str
    created_at: str
    items: list[ReceiptItemResponse] = []

    model_config = {"from_attributes": True}


class OCRResult(BaseModel):
    raw_text: str
    supplier_name: str | None
    receipt_date: str | None
    total_amount: float
    items: list[ReceiptItemCreate]
