from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.category import Category
from app.schemas.category import CategoryCreate, CategoryResponse
from app.services.auth_service import get_current_user

router = APIRouter(prefix="/api/categories", tags=["Categories"])


@router.get("", response_model=list[CategoryResponse])
def list_categories(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    categories = db.query(Category).filter(Category.user_id == user.id).all()
    return [CategoryResponse.model_validate(c) for c in categories]


@router.post("", response_model=CategoryResponse)
def create_category(
    data: CategoryCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    category = Category(name=data.name, user_id=user.id)
    db.add(category)
    db.commit()
    db.refresh(category)
    return CategoryResponse.model_validate(category)


@router.delete("/{category_id}")
def delete_category(
    category_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    category = db.query(Category).filter(
        Category.id == category_id, Category.user_id == user.id
    ).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    db.delete(category)
    db.commit()
    return {"message": "Category deleted"}
