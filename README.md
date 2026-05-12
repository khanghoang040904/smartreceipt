# SmartReceipt — AI-Powered Expense Management for Small Businesses

A web application that helps small business owners digitize paper receipts using AI-powered OCR (Optical Character Recognition), categorize expenses, and visualize spending trends.

## Features

- **Receipt OCR**: Upload receipt images and automatically extract text using EasyOCR
- **Structured Data Extraction**: Parse supplier name, date, total amount, and item details
- **Expense Categorization**: Organize receipts by categories (Food, Beverages, Supplies, etc.)
- **Dashboard Analytics**: Visualize spending by category and over time with interactive charts
- **Receipt History**: Search and filter past receipts
- **CSV Export**: Export expense data for use in Excel or other tools

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React (Vite) + TailwindCSS |
| Backend | FastAPI (Python) |
| OCR Engine | EasyOCR |
| Database | SQLite + SQLAlchemy |
| Charts | Recharts |

## Project Structure

```
smartreceipt/
├── frontend/          # React (Vite) frontend
├── backend/           # FastAPI backend
│   ├── app/
│   │   ├── controllers/
│   │   ├── services/
│   │   ├── repositories/
│   │   ├── models/
│   │   └── schemas/
│   ├── tests/
│   └── uploads/
└── docs/              # Documentation
```

## Getting Started

### Prerequisites

- Python 3.10+
- Node.js 18+
- npm or yarn

### Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

## License

This project is for educational purposes (Software Engineering Course - Mid-term Project).
