---
name: testing-smartreceipt
description: Test the SmartReceipt expense management app end-to-end. Use when verifying auth, OCR, dashboard, or receipt management changes.
---

# Testing SmartReceipt

## Prerequisites

- Python 3.12+ with venv
- Node.js 18+
- Test receipt image (generate with Pillow if not available)

## Setup

### Backend (FastAPI)
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
# Delete old DB for clean test state
rm -f smartreceipt.db
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Frontend (Next.js)
```bash
cd frontend
npm install
npm run dev
# Runs on port 3000 by default
```

### Important Notes
- The venv may be missing after system restarts — recreate it
- If port 3000 is already in use, an old Next.js process may still be running. Kill it or use the existing one.
- EasyOCR downloads models on first use (~100MB). First OCR request may take 15-30 seconds.
- Backend creates SQLite DB automatically on first request

## Test Receipt Image
If `/home/ubuntu/test_receipt.png` doesn't exist, generate one:
```python
from PIL import Image, ImageDraw, ImageFont
img = Image.new('RGB', (400, 600), 'white')
draw = ImageDraw.Draw(img)
lines = [
    "CUA HANG TAPHOA ABC", "123 Nguyen Trai, Q5, TPHCM",
    "Ngay 15/05/2025", "Hoa don so HD001",
    "Gao ST25 5kg  1  185000", "Nuoc mam  2  45000",
    "Dau an  1  62000", "Tong cong  337,000d"
]
for i, line in enumerate(lines):
    draw.text((20, 30 + i * 40), line, fill='black')
img.save('/home/ubuntu/test_receipt.png')
```

## File Upload via Playwright CDP
The file input cannot be interacted with via native GUI file dialogs. Use Playwright CDP:
```python
import asyncio
from playwright.async_api import async_playwright

async def upload_file():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://localhost:29229")
        context = browser.contexts[0]
        page = context.pages[0]
        await page.keyboard.press("Escape")  # Close any open dialog
        await asyncio.sleep(1)
        # Use the file input inside main content area (there may be multiple)
        file_input = page.get_by_role("main").locator('input[type="file"]')
        await file_input.set_input_files("/home/ubuntu/test_receipt.png")
        await asyncio.sleep(15)  # Wait for OCR processing

asyncio.run(upload_file())
```
**Note**: There might be multiple `input[type="file"]` elements. Scope to `get_by_role("main")` to avoid strict mode violations.

## Key Test Flows

### 1. Login Error Handling (auth endpoint fix)
- Navigate to `/login`
- Enter wrong credentials (e.g., `wrong@test.com` / `WrongPass1`)
- **Expected**: Red "Invalid credentials" banner appears inline. Page does NOT reload. Fields stay filled.
- **If broken**: Page reloads to fresh login form (old behavior where 401 interceptor caught auth errors)

### 2. Full E2E: Register → Upload → Dashboard → History
- Register at `/register` (e.g., `test@demo.com` / `Test User` / `Test1234`)
- Navigate to Upload Receipt, upload test image
- Wait for OCR (~15s), verify supplier name extracted
- Click "Lưu hóa đơn" → button changes to "Đã lưu!"
- Check Dashboard: Total Receipts should increment
- Check Receipt History: receipt row with supplier name
- Click eye icon: detail page shows image + raw OCR text

### 3. Logout/Re-login Persistence
- Click Logout in sidebar → redirects to `/login`
- Login with same credentials → dashboard shows same receipt count

## Backend Tests
```bash
cd backend
source venv/bin/activate
python -m pytest tests/ -v
# All 15 tests should pass
```

## Common Issues
- **bcrypt version**: Must use bcrypt==4.2.1 (pinned in requirements.txt). Version 5.x breaks passlib.
- **model_fields_set regression**: If partial updates crash with IntegrityError, check that NOT NULL columns (total_amount, status) have `is not None` guards in receipt_controller.py
- **CORS**: Only localhost:3000 and localhost:5173 are allowed (no wildcard with credentials)

## Devin Secrets Needed
No external secrets required — the app uses local SQLite and EasyOCR (offline).
