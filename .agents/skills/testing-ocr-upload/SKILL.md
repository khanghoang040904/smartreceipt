---
name: testing-ocr-upload
description: Test the SmartReceipt OCR receipt upload flow end-to-end. Use when verifying OCR parsing, supplier name extraction, or total amount extraction changes.
---

# Testing SmartReceipt OCR Upload

## Prerequisites

### Start Backend
```bash
cd /home/ubuntu/repos/smartreceipt/backend
source venv/bin/activate
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Start Frontend
```bash
cd /home/ubuntu/repos/smartreceipt/frontend
npm run dev
```

### Verify servers
- Backend: `curl -s http://localhost:8000/docs` should return 200
- Frontend: `curl -s http://localhost:3000/login` should return 200

### Important: Database Reset
If you delete the database (`smartreceipt.db`), you MUST recreate tables before starting the backend:
```python
from app.database import engine, Base
from app.models.user import User
from app.models.receipt import Receipt
from app.models.category import Category
Base.metadata.create_all(bind=engine)
```
Otherwise the backend will return 500 Internal Server Error on all API calls.

### Important: Backend Restart After Code Changes
Python caches imported modules. If you modify `ocr_service.py` or any backend file, you MUST restart the uvicorn process for changes to take effect. Kill the old process first, then start a new one.

## Test Flow

1. **Register/Login**: Navigate to `localhost:3000/register` or `localhost:3000/login`
2. **Navigate to Upload**: Click "Upload Receipt" in the sidebar
3. **Upload receipt image**: Use Playwright to set the file input since native file dialogs can't be controlled:
   ```python
   import asyncio
   from playwright.async_api import async_playwright

   async def upload_file(filepath):
       async with async_playwright() as p:
           browser = await p.chromium.connect_over_cdp("http://localhost:29229")
           context = browser.contexts[0]
           page = context.pages[0]
           file_input = page.get_by_role("main").locator('input[type="file"]')
           await file_input.set_input_files(filepath)

   asyncio.run(upload_file("/path/to/receipt.png"))
   ```
4. **Wait for OCR**: EasyOCR processing takes 10-20 seconds per image
5. **Verify results**: Check the "Thông tin trích xuất" section:
   - "Nhà cung cấp" (supplier name) input field
   - "Tổng tiền" (total amount) number input field
   - "Ngày" (date) text input field
6. **Reset**: Click "Upload mới" button to upload another receipt

## Common OCR Issues

- **EasyOCR fragments text**: Multi-word business names may be split across lines (e.g., "DIEN" / "MAY" / "XANH"). The `_extract_supplier()` function in `ocr_service.py` handles this by combining fragments until it hits addresses/phone/separators.
- **Spaces in numbers**: OCR might produce "216 , 000" instead of "216,000". The `_normalize_ocr_text()` function handles this.
- **Non-diacritical Vietnamese**: OCR often strips accents ("THANH TOAN" instead of "Thanh toán"). Total patterns must include both diacritical and non-diacritical variants.
- **Multi-line keywords**: The total amount keyword and value might be on different lines. The parser joins all lines into a single string for matching.

## Demo Receipt Images

Demo receipts are generated in `/home/ubuntu/demo_receipts/`. If they don't exist, you can regenerate them using the generation scripts. Expected values:

| Receipt | Expected Supplier | Expected Total |
|---------|------------------|---------------|
| receipt_coffeeshop.png | THE COFFEE HOUSE | 216,000 |
| receipt_restaurant.png | NHA HANG HAI SAN BIEN DONG | 1,197,800 |
| receipt_supermarket.png | SIEU THI CO. OPMART | 575,225 |
| receipt_electronics.png | DIEN MAY XANH | 8,760,000 |
| receipt_pharmacy.png | NHA THUOC AN KHANG | 220,000 |
| receipt_camera_style.png | BACH HOA XANH | 531,000 |

## Unit Tests
```bash
cd /home/ubuntu/repos/smartreceipt/backend
source venv/bin/activate
python -m pytest tests/ -v
```
Expected: 15 tests passing.

## Devin Secrets Needed
No secrets required — the app runs entirely locally with SQLite.
