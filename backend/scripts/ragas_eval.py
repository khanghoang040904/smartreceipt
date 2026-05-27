"""Ragas evaluation for SmartReceipt RAG chatbot.

Run: cd backend && python scripts/ragas_eval.py

Requires:
  - GEMINI_API_KEY set in backend/.env
  - Test receipt images in the Test/ folder
  - ragas, datasets, langchain-google-genai packages installed
"""
from __future__ import annotations

import json
import logging
import os
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv

env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(env_path)

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# ── Setup DB + services ──────────────────────────────────────────────
from app.database import engine, Base, SessionLocal
from app.models.receipt import Receipt, ReceiptItem
from app.models.user import User
from app.models.category import Category
from app.services.ocr_service import process_receipt
from app.services.receipt_index_service import receipt_index_service, build_receipt_chunks
from app.services.chat_service import answer_chat
from app.schemas.chat import ChatRequest

Base.metadata.create_all(bind=engine)

TEST_DIR = os.environ.get(
    "TEST_RECEIPTS_DIR",
    str(Path(__file__).resolve().parent.parent.parent.parent
        / "attachments" / "4aa19db7-f667-49ff-9e9b-e47fc9ede1f5" / "Test"),
)

# ── Evaluation dataset ───────────────────────────────────────────────
# Ground-truth Q&A pairs based on typical receipt queries
EVAL_QUESTIONS = [
    {
        "question": "Tổng chi tiêu bao nhiêu?",
        "ground_truth": "Tổng chi tiêu là tổng số tiền tất cả các hóa đơn đã tải lên.",
        "expected_keywords": ["tổng", "chi tiêu", "đ"],
    },
    {
        "question": "Hóa đơn nào có tổng tiền cao nhất?",
        "ground_truth": "Hóa đơn có tổng tiền cao nhất cần được xác định từ danh sách.",
        "expected_keywords": ["cao nhất", "hóa đơn"],
    },
    {
        "question": "Có bao nhiêu hóa đơn?",
        "ground_truth": "Số lượng hóa đơn tương ứng với số file test đã upload.",
        "expected_keywords": ["hóa đơn"],
    },
    {
        "question": "Liệt kê nhà cung cấp của các hóa đơn",
        "ground_truth": "Danh sách nhà cung cấp từ các hóa đơn đã upload.",
        "expected_keywords": ["nhà cung cấp"],
    },
    {
        "question": "Hóa đơn nào mua cà phê?",
        "ground_truth": "Hóa đơn từ quán cà phê hoặc có sản phẩm cà phê.",
        "expected_keywords": ["cà phê"],
    },
]


def seed_test_data(db):
    """Upload test receipts and index them."""
    # Create test user
    user = db.query(User).filter(User.email == "ragas_test@test.com").first()
    if not user:
        from app.services.auth_service import hash_password
        user = User(
            email="ragas_test@test.com",
            full_name="Ragas Test User",
            password_hash=hash_password("test123"),
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    # Check if already seeded
    existing = db.query(Receipt).filter(Receipt.user_id == user.id).count()
    if existing > 0:
        logger.info("Test data already exists (%d receipts). Skipping seed.", existing)
        return user

    # Process each test receipt
    if not os.path.isdir(TEST_DIR):
        logger.error("Test receipts directory not found: %s", TEST_DIR)
        sys.exit(1)

    image_files = sorted(
        f for f in os.listdir(TEST_DIR)
        if f.lower().endswith((".png", ".jpg", ".jpeg"))
    )
    logger.info("Found %d test receipt images in %s", len(image_files), TEST_DIR)

    for img_file in image_files:
        img_path = os.path.join(TEST_DIR, img_file)
        logger.info("Processing: %s", img_file)
        try:
            parsed = process_receipt(img_path)
        except Exception:
            logger.exception("Failed to process %s", img_file)
            continue

        receipt = Receipt(
            user_id=user.id,
            image_path=img_file,
            raw_text=parsed.get("raw_text", ""),
            supplier_name=parsed.get("supplier_name"),
            receipt_date=parsed.get("receipt_date"),
            total_amount=parsed.get("total_amount", 0),
            vat_amount=parsed.get("vat_amount", 0),
            discount_amount=parsed.get("discount_amount", 0),
            status="Đã duyệt",
        )
        db.add(receipt)
        db.commit()
        db.refresh(receipt)

        for item_data in parsed.get("items", []):
            item = ReceiptItem(
                receipt_id=receipt.id,
                item_name=item_data.get("item_name", ""),
                quantity=item_data.get("quantity", 1),
                unit_price=item_data.get("unit_price", 0),
                amount=item_data.get("amount", 0),
            )
            db.add(item)
        db.commit()

        receipt_index_service.upsert_receipt(receipt)
        logger.info(
            "  -> Receipt #%d: %s, %s, %.0f đ, %d items",
            receipt.id,
            receipt.supplier_name or "?",
            receipt.receipt_date or "?",
            receipt.total_amount or 0,
            len(parsed.get("items", [])),
        )

    total = db.query(Receipt).filter(Receipt.user_id == user.id).count()
    logger.info("Seeded %d receipts for user %d", total, user.id)
    return user


def evaluate_retrieval(db, user):
    """Evaluate retrieval quality: check if relevant receipts are retrieved."""
    logger.info("\n" + "=" * 60)
    logger.info("RETRIEVAL EVALUATION")
    logger.info("=" * 60)

    all_receipts = db.query(Receipt).filter(Receipt.user_id == user.id).all()
    logger.info("Total receipts in DB: %d", len(all_receipts))

    results = []
    for qa in EVAL_QUESTIONS:
        question = qa["question"]
        search_results = receipt_index_service.search(
            db=db, user_id=user.id, query=question, limit=6
        )
        retrieved_ids = [r.receipt_id for r in search_results]
        scores = [r.score for r in search_results]
        avg_score = sum(scores) / len(scores) if scores else 0
        above_threshold = sum(1 for s in scores if s >= 0.3)

        result = {
            "question": question,
            "retrieved_count": len(search_results),
            "above_threshold": above_threshold,
            "avg_score": round(avg_score, 3),
            "max_score": round(max(scores), 3) if scores else 0,
            "min_score": round(min(scores), 3) if scores else 0,
        }
        results.append(result)
        logger.info(
            "  Q: %s\n    Retrieved: %d | Above 0.3: %d | Avg: %.3f | Max: %.3f",
            question, len(search_results), above_threshold, avg_score,
            max(scores) if scores else 0,
        )

    avg_retrieval_score = sum(r["avg_score"] for r in results) / len(results)
    avg_above_threshold = sum(r["above_threshold"] for r in results) / len(results)
    logger.info("\nRetrieval Summary:")
    logger.info("  Average score: %.3f", avg_retrieval_score)
    logger.info("  Average results above threshold: %.1f", avg_above_threshold)
    return results, avg_retrieval_score


def evaluate_generation(db, user):
    """Evaluate answer generation quality."""
    logger.info("\n" + "=" * 60)
    logger.info("GENERATION EVALUATION (RAG + Gemini)")
    logger.info("=" * 60)

    results = []
    for qa in EVAL_QUESTIONS:
        question = qa["question"]
        expected_keywords = qa["expected_keywords"]

        request = ChatRequest(message=question)
        try:
            response = answer_chat(request, user.id, db)
        except Exception:
            logger.exception("Chat failed for: %s", question)
            results.append({
                "question": question,
                "answer": "ERROR",
                "keyword_match": 0,
                "has_sources": False,
                "source_count": 0,
                "confidence": 0,
            })
            continue

        answer_lower = response.answer.lower()
        matched = sum(1 for kw in expected_keywords if kw.lower() in answer_lower)
        keyword_score = matched / len(expected_keywords) if expected_keywords else 1

        result = {
            "question": question,
            "answer": response.answer[:200],
            "keyword_match": round(keyword_score, 2),
            "has_sources": len(response.sources) > 0,
            "source_count": len(response.sources),
            "confidence": response.confidence,
        }
        results.append(result)
        logger.info(
            "  Q: %s\n    A: %s...\n    Keywords: %.0f%% | Sources: %d | Conf: %.1f",
            question, response.answer[:100],
            keyword_score * 100, len(response.sources), response.confidence,
        )

    avg_keyword = sum(r["keyword_match"] for r in results) / len(results)
    avg_sources = sum(r["source_count"] for r in results) / len(results)
    avg_confidence = sum(r["confidence"] for r in results) / len(results)

    logger.info("\nGeneration Summary:")
    logger.info("  Average keyword match: %.1f%%", avg_keyword * 100)
    logger.info("  Average sources per answer: %.1f", avg_sources)
    logger.info("  Average confidence: %.2f", avg_confidence)
    return results, avg_keyword


def evaluate_with_ragas(db, user):
    """Run Ragas evaluation if possible."""
    logger.info("\n" + "=" * 60)
    logger.info("RAGAS FRAMEWORK EVALUATION")
    logger.info("=" * 60)

    try:
        from ragas import evaluate as ragas_evaluate
        from ragas.metrics import faithfulness, answer_relevancy, context_precision, context_recall
        from ragas import EvaluationDataset, SingleTurnSample
        from langchain_google_genai import ChatGoogleGenerativeAI
    except ImportError as e:
        logger.warning("Ragas dependencies not available: %s. Skipping framework eval.", e)
        return None

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        logger.warning("GEMINI_API_KEY not set. Skipping Ragas eval.")
        return None

    samples = []
    for qa in EVAL_QUESTIONS:
        question = qa["question"]

        # Get retrieval context
        search_results = receipt_index_service.search(
            db=db, user_id=user.id, query=question, limit=6
        )
        contexts = [r.chunk_text for r in search_results if r.score >= 0.3]
        if not contexts:
            contexts = [r.chunk_text for r in search_results[:3]]

        # Get generated answer
        request = ChatRequest(message=question)
        try:
            response = answer_chat(request, user.id, db)
            answer = response.answer
        except Exception:
            answer = "Lỗi khi tạo câu trả lời."

        samples.append(
            SingleTurnSample(
                user_input=question,
                retrieved_contexts=contexts,
                response=answer,
                reference=qa["ground_truth"],
            )
        )

    dataset = EvaluationDataset(samples=samples)

    llm = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash",
        google_api_key=api_key,
    )

    try:
        ragas_result = ragas_evaluate(
            dataset=dataset,
            metrics=[faithfulness, answer_relevancy, context_precision, context_recall],
            llm=llm,
        )
        logger.info("\nRagas Results:")
        for metric, value in ragas_result.items():
            if isinstance(value, (int, float)):
                logger.info("  %s: %.3f", metric, value)
        return ragas_result
    except Exception:
        logger.exception("Ragas evaluation failed")
        return None


def generate_report(retrieval_results, retrieval_avg, generation_results, gen_avg, ragas_result):
    """Generate a summary report."""
    report = {
        "retrieval": {
            "average_score": round(retrieval_avg, 3),
            "details": retrieval_results,
        },
        "generation": {
            "average_keyword_match": round(gen_avg, 2),
            "details": generation_results,
        },
        "ragas": ragas_result if ragas_result else "Skipped or failed",
        "recommendations": [],
    }

    if retrieval_avg < 0.4:
        report["recommendations"].append(
            "Retrieval scores are low. Consider: "
            "(1) Adding Vietnamese-optimized embeddings, "
            "(2) Enriching chunk text with Vietnamese metadata, "
            "(3) Using a multilingual embedding model."
        )
    if gen_avg < 0.6:
        report["recommendations"].append(
            "Generation keyword match is low. Consider: "
            "(1) Improving the system prompt for Gemini, "
            "(2) Adding few-shot examples in the chat prompt."
        )

    report_path = Path(__file__).parent / "ragas_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    logger.info("\nReport saved to: %s", report_path)
    return report


def main():
    db = SessionLocal()
    try:
        logger.info("=== SmartReceipt RAG Evaluation ===\n")

        # Step 1: Seed test data
        user = seed_test_data(db)

        # Step 2: Evaluate retrieval
        retrieval_results, retrieval_avg = evaluate_retrieval(db, user)

        # Step 3: Evaluate generation
        gen_results, gen_avg = evaluate_generation(db, user)

        # Step 4: Run Ragas framework evaluation
        ragas_result = evaluate_with_ragas(db, user)

        # Step 5: Generate report
        report = generate_report(retrieval_results, retrieval_avg, gen_results, gen_avg, ragas_result)

        # Final summary
        logger.info("\n" + "=" * 60)
        logger.info("FINAL SUMMARY")
        logger.info("=" * 60)
        logger.info("  Retrieval avg score: %.3f %s",
                     retrieval_avg, "OK" if retrieval_avg >= 0.4 else "NEEDS IMPROVEMENT")
        logger.info("  Generation keyword match: %.1f%% %s",
                     gen_avg * 100, "OK" if gen_avg >= 0.6 else "NEEDS IMPROVEMENT")
        if report["recommendations"]:
            logger.info("\nRecommendations:")
            for rec in report["recommendations"]:
                logger.info("  - %s", rec)
        else:
            logger.info("\nAll metrics look good!")

    finally:
        db.close()


if __name__ == "__main__":
    main()
