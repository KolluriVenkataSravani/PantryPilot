from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from app import repository
from app.database import get_db
from app.schemas import ItemCreate, ItemRead, PantrySummary


router = APIRouter(prefix="/api")


@router.get("/items", response_model=list[ItemRead])
def read_items(
    q: str | None = Query(default=None, max_length=120),
    status_filter: Literal["expired", "expiring", "fresh"] | None = Query(
        default=None, alias="status"
    ),
    db: Session = Depends(get_db),
) -> list[ItemRead]:
    return repository.list_items(db, search=q, status=status_filter)


@router.post("/items", response_model=ItemRead, status_code=status.HTTP_201_CREATED)
def create_item(item: ItemCreate, db: Session = Depends(get_db)) -> ItemRead:
    return repository.add_item(db, item)


@router.put("/items/{item_id}", response_model=ItemRead)
def edit_item(item_id: int, item: ItemCreate, db: Session = Depends(get_db)) -> ItemRead:
    updated_item = repository.update_item(db, item_id, item)
    if updated_item is None:
        raise HTTPException(status_code=404, detail="Pantry item not found")
    return updated_item


@router.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_item(item_id: int, db: Session = Depends(get_db)) -> Response:
    if not repository.delete_item(db, item_id):
        raise HTTPException(status_code=404, detail="Pantry item not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/summary", response_model=PantrySummary)
def read_summary(db: Session = Depends(get_db)) -> PantrySummary:
    return repository.get_summary(db)


@router.get("/health")
def read_health(db: Session = Depends(get_db)) -> dict[str, str]:
    db.execute(text("SELECT 1"))
    return {"status": "ok"}
