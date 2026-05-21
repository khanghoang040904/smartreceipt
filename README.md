# SmartReceipt — AI-Powered Expense Management for Small Businesses

A web application that helps small business owners digitize paper receipts using AI-powered OCR (Optical Character Recognition), categorize expenses, and visualize spending trends.

## Features

- **Receipt OCR**: Upload receipt images and automatically extract text using EasyOCR
- **Structured Data Extraction**: Parse supplier name, date, total amount, and item details
- **Expense Categorization**: Organize receipts by categories (Food, Beverages, Supplies, etc.)
- **Dashboard Analytics**: Visualize spending by category and over time with interactive charts
- **Receipt History**: Search and filter past receipts
- **Receipt Assistant**: Ask Vietnamese questions about saved receipts, totals, suppliers, and items
- **Budget Tracking**: Set monthly category budgets and compare them with actual spending
- **CSV Export**: Export expense data for use in Excel or other tools

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js + React + TailwindCSS |
| Backend | FastAPI (Python) |
| OCR Engine | EasyOCR |
| Database | SQLite + SQLAlchemy |
| Local Search | Chroma + SentenceTransformers |
| Charts | Recharts |

## Project Structure

```
smartreceipt/
├── frontend/          # Next.js frontend
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

- Python 3.12 recommended
- Node.js 18+
- npm or yarn

### Backend Setup

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Local Data Storage

SmartReceipt stores data locally by default. The backend uses SQLite through
`DATABASE_URL`; if it is not set, the app writes to `backend/smartreceipt.db`
when you start the server from the `backend` folder. Uploaded receipt images are
stored in `backend/uploads`, and the local chat vector index is stored in
`backend/vectorstore`. Firebase is not used unless you explicitly replace the
database configuration.

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

## License

This project is for educational purposes (Software Engineering Course - Mid-term Project).
