from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.database import engine, Base
from app.config import UPLOAD_DIR
from app.controllers import auth_controller, receipt_controller, category_controller, dashboard_controller, export_controller, chat_controller, budget_controller

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="SmartReceipt API",
    description="AI-Powered Expense Management for Small Businesses",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

app.include_router(auth_controller.router)
app.include_router(receipt_controller.router)
app.include_router(category_controller.router)
app.include_router(dashboard_controller.router)
app.include_router(export_controller.router)
app.include_router(chat_controller.router)
app.include_router(budget_controller.router)


@app.get("/")
def root():
    return {"message": "SmartReceipt API is running", "docs": "/docs"}
