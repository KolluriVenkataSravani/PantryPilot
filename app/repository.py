from datetime import date, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import PantryItem
from app.schemas import ItemCreate


def list_items(
    db: Session, search: str | None = None, status: str | None = None
) -> list[PantryItem]:
    today = date.today()
    query = select(PantryItem)

    if search:
        query = query.where(PantryItem.name.ilike(f"%{search.strip()}%"))
    if status == "expired":
        query = query.where(PantryItem.expires_on < today)
    elif status == "expiring":
        query = query.where(
            PantryItem.expires_on >= today,
            PantryItem.expires_on <= today + timedelta(days=7),
        )
    elif status == "fresh":
        query = query.where(
            (PantryItem.expires_on.is_(None))
            | (PantryItem.expires_on > today + timedelta(days=7))
        )

    query = query.order_by(
        PantryItem.expires_on.is_(None), PantryItem.expires_on, PantryItem.name
    )
    return list(db.scalars(query))


def add_item(db: Session, item: ItemCreate) -> PantryItem:
    pantry_item = PantryItem(**item.model_dump())
    db.add(pantry_item)
    db.commit()
    db.refresh(pantry_item)
    return pantry_item


def update_item(db: Session, item_id: int, item: ItemCreate) -> PantryItem | None:
    pantry_item = db.get(PantryItem, item_id)
    if pantry_item is None:
        return None
    for field, value in item.model_dump().items():
        setattr(pantry_item, field, value)
    db.commit()
    db.refresh(pantry_item)
    return pantry_item


def delete_item(db: Session, item_id: int) -> bool:
    item = db.get(PantryItem, item_id)
    if item is None:
        return False
    db.delete(item)
    db.commit()
    return True


def get_summary(db: Session) -> dict[str, int]:
    today = date.today()
    soon = today + timedelta(days=7)
    total = db.scalar(select(func.count()).select_from(PantryItem)) or 0
    expired = db.scalar(
        select(func.count()).select_from(PantryItem).where(PantryItem.expires_on < today)
    ) or 0
    expiring = db.scalar(
        select(func.count())
        .select_from(PantryItem)
        .where(PantryItem.expires_on >= today, PantryItem.expires_on <= soon)
    ) or 0
    return {"total_items": total, "expiring_soon": expiring, "expired": expired}
