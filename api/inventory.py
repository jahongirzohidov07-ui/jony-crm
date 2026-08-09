"""Auto-extracted from main.py during refactor (split-main). Domain: inventory."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import bisect
from datetime import date, datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy import func, or_, text
from sqlalchemy.orm import Session

import audit
import billing
import migrations
import models
import notify
import roles
import schemas
from auth import (
    create_access_token,
    get_current_user,
    hash_password,
    require_role,
    verify_password,
    SECRET_KEY,
)
from database import Base, engine, get_db, SessionLocal
from common import *  # noqa: F401,F403 - shared helpers/state

router = APIRouter()

def _next_inventory_no(db: Session, kind: str) -> str:
    """Inventar raqami: "AC-0007". Turi bo'yicha ketma-ket boradi."""
    prefix = {
        "computer": "PC", "laptop": "NB", "tv": "TV", "projector": "PR",
        "printer": "PT", "furniture": "FR", "camera": "CM",
        "phone": "PH", "ac": "AC", "router": "RT", "other": "OT",
    }.get(kind, "OT")
    n = db.query(models.Asset).filter(models.Asset.kind == kind).count() + 1
    while db.query(models.Asset).filter(
            models.Asset.inventory_no == f"{prefix}-{n:04d}").first():
        n += 1
    return f"{prefix}-{n:04d}"

def _asset_out(db: Session, a: models.Asset) -> dict:
    reps = sorted(a.repairs, key=lambda r: r.happened_on or date.min,
                  reverse=True)
    return {
        "id": a.id,
        "inventory_no": a.inventory_no,
        "name": a.name,
        "kind": a.kind,
        "kind_label": roles.ASSET_TYPE_LABELS.get(a.kind, a.kind),
        "branch_id": a.branch_id,
        "branch": a.branch.name if a.branch else None,
        "room_id": a.room_id,
        "room": a.room.name if a.room else None,
        "responsible_id": a.responsible_id,
        "responsible": a.responsible.full_name if a.responsible else None,
        "purchased_on": a.purchased_on.isoformat() if a.purchased_on else None,
        "price": a.price,
        "condition": a.condition,
        "condition_label": roles.ASSET_CONDITION_LABELS.get(a.condition, a.condition),
        "condition_tone": roles.ASSET_CONDITION_TONE.get(a.condition, "slate"),
        "warranty_until": a.warranty_until.isoformat() if a.warranty_until else None,
        "warranty_active": bool(a.warranty_until and a.warranty_until >= date.today()),
        "serial_no": a.serial_no,
        "photo": a.photo,
        "note": a.note,
        "written_off_on": a.written_off_on.isoformat() if a.written_off_on else None,
        "repairs": [{
            "id": r.id,
            "date": r.happened_on.isoformat() if r.happened_on else None,
            "cost": r.cost, "vendor": r.vendor, "note": r.note,
        } for r in reps],
        "repair_count": len(reps),
        "repair_cost": round(sum(r.cost or 0 for r in reps), 2),
        # Ta'mir narxi jihoz narxining yarmidan oshsa - almashtirish arzon.
        "replace_hint": bool(
            a.price and sum(r.cost or 0 for r in reps) > a.price * 0.5),
    }

@router.get("/api/assets")
def list_assets(
    branch_id: Optional[int] = None,
    kind: Optional[str] = None,
    condition: Optional[str] = None,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.INVENTORY_VIEW)),
):
    q = scope_to_branch(db.query(models.Asset), models.Asset, user, branch_id)
    if kind:
        q = q.filter(models.Asset.kind == kind)
    if condition:
        q = q.filter(models.Asset.condition == condition)
    rows = [_asset_out(db, a) for a in q.order_by(models.Asset.inventory_no).all()]

    return {
        "rows": rows,
        "total_value": round(sum(r["price"] or 0 for r in rows), 2),
        "count": len(rows),
        "needs_attention": sum(1 for r in rows
                               if r["condition"] in ("repair", "broken")),
        "kinds": [{"key": k, "label": lbl,
                   "count": sum(1 for r in rows if r["kind"] == k)}
                  for k, lbl in roles.ASSET_TYPES],
        "conditions": [{"key": k, "label": lbl, "tone": t,
                        "count": sum(1 for r in rows if r["condition"] == k)}
                       for k, lbl, t in roles.ASSET_CONDITIONS],
        "can_edit": user.role in tuple(roles.INVENTORY_ACCESS),
    }

@router.post("/api/assets")
def create_asset(
    payload: schemas.AssetCreate,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.INVENTORY_ACCESS)),
):
    if payload.kind not in roles.ASSET_TYPE_LABELS:
        raise HTTPException(400, "Noto'g'ri aktiv turi")
    if payload.condition not in roles.ASSET_CONDITION_LABELS:
        raise HTTPException(400, "Noto'g'ri holat")
    if payload.photo and len(payload.photo) > roles.ATTACHMENT_MAX_BYTES:
        raise HTTPException(400, "Rasm juda katta (3 MB dan oshmasin)")

    data = payload.model_dump()
    if user.role not in tuple(roles.ORG_WIDE_ROLES) and user.branch_id:
        data["branch_id"] = user.branch_id
    a = models.Asset(**data)
    a.inventory_no = a.inventory_no or _next_inventory_no(db, a.kind)
    db.add(a); db.commit(); db.refresh(a)
    audit.log(db, user, entity="asset", action="create", entity_id=a.id,
              entity_label=f"{a.inventory_no} {a.name}", branch_id=a.branch_id,
              new_value=a.name)
    db.commit()
    return _asset_out(db, a)

@router.put("/api/assets/{asset_id}")
def update_asset(
    asset_id: int,
    payload: schemas.AssetUpdate,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.INVENTORY_ACCESS)),
):
    a = db.query(models.Asset).get(asset_id)
    if not a:
        raise HTTPException(404, "Aktiv topilmadi")
    fields = payload.model_dump(exclude_unset=True)
    if fields.get("photo") and len(fields["photo"]) > roles.ATTACHMENT_MAX_BYTES:
        raise HTTPException(400, "Rasm juda katta (3 MB dan oshmasin)")
    audit.log_changes(db, user, entity="asset", obj=a,
                      changes={k: v for k, v in fields.items()
                               if k in ("condition", "responsible_id",
                                        "room_id", "branch_id")})
    for k, v in fields.items():
        setattr(a, k, v)
    # Hisobdan chiqarilgan bo'lsa sanani avtomat qo'yamiz.
    if a.condition == "written_off" and not a.written_off_on:
        a.written_off_on = date.today()
    elif a.condition != "written_off":
        a.written_off_on = None
    db.commit(); db.refresh(a)
    return _asset_out(db, a)

@router.delete("/api/assets/{asset_id}")
def delete_asset(
    asset_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.FULL_ACCESS)),
):
    a = db.query(models.Asset).get(asset_id)
    if not a:
        raise HTTPException(404, "Aktiv topilmadi")
    audit.log(db, user, entity="asset", action="delete", entity_id=a.id,
              entity_label=f"{a.inventory_no} {a.name}",
              branch_id=a.branch_id, old_value=a.name)
    db.delete(a); db.commit()
    return {"ok": True}

@router.post("/api/assets/{asset_id}/repairs")
def add_repair(
    asset_id: int,
    payload: schemas.RepairCreate,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.INVENTORY_ACCESS)),
):
    a = db.query(models.Asset).get(asset_id)
    if not a:
        raise HTTPException(404, "Aktiv topilmadi")
    r = models.AssetRepair(
        asset_id=asset_id, happened_on=payload.date or date.today(),
        cost=payload.cost or 0, vendor=payload.vendor, note=payload.note,
        created_by=user.full_name)
    db.add(r)
    # Ta'mirga berilgan jihoz "ta'mirda" bo'ladi.
    if a.condition not in ("written_off",):
        a.condition = "repair"
    db.commit(); db.refresh(a)
    return _asset_out(db, a)

@router.post("/api/assets/repairs/{repair_id}/done")
def finish_repair(
    repair_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.INVENTORY_ACCESS)),
):
    r = db.query(models.AssetRepair).get(repair_id)
    if not r:
        raise HTTPException(404, "Topilmadi")
    a = db.query(models.Asset).get(r.asset_id)
    if a and a.condition == "repair":
        a.condition = "good"
    db.commit()
    return _asset_out(db, a) if a else {"ok": True}

def _check_stock(db: Session, c: models.Consumable) -> models.PurchaseRequest | None:
    """AVTOMAT: qoldiq minimaldan pastga tushsa xarid so'rovi yaratiladi.
    Ochiq so'rov allaqachon bo'lsa takror yaratilmaydi - shunda ro'yxat
    bir xil so'rovlar bilan to'lib ketmaydi."""
    if c.min_qty is None or c.qty > c.min_qty:
        return None
    exists = (db.query(models.PurchaseRequest)
              .filter(models.PurchaseRequest.consumable_id == c.id,
                      models.PurchaseRequest.status == "open").first())
    if exists:
        return exists
    # Minimalning ikki barobariga to'ldiramiz - tez-tez so'rov qilmaslik uchun
    need = max(1.0, (c.min_qty or 1) * 2 - c.qty)
    pr = models.PurchaseRequest(
        consumable_id=c.id, qty=need, auto=1,
        note=f"Qoldiq {c.qty} {c.unit or 'dona'}, minimal {c.min_qty}")
    db.add(pr)
    return pr

def _consumable_out(db: Session, c: models.Consumable) -> dict:
    low = c.min_qty is not None and c.qty <= c.min_qty
    open_pr = (db.query(models.PurchaseRequest)
               .filter(models.PurchaseRequest.consumable_id == c.id,
                       models.PurchaseRequest.status == "open").first())
    return {
        "id": c.id,
        "name": c.name,
        "kind": c.kind,
        "kind_label": roles.CONSUMABLE_TYPE_LABELS.get(c.kind, c.kind),
        "branch_id": c.branch_id,
        "branch": c.branch.name if c.branch else None,
        "qty": c.qty,
        "min_qty": c.min_qty,
        "unit": c.unit or roles.CONSUMABLE_UNITS.get(c.kind, "dona"),
        "unit_price": c.unit_price,
        "value": round((c.qty or 0) * (c.unit_price or 0), 2),
        "low": low,
        "note": c.note,
        "request_id": open_pr.id if open_pr else None,
        "request_qty": open_pr.qty if open_pr else None,
    }

@router.get("/api/consumables")
def list_consumables(
    branch_id: Optional[int] = None,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.INVENTORY_VIEW)),
):
    q = scope_to_branch(db.query(models.Consumable), models.Consumable,
                        user, branch_id)
    items = q.order_by(models.Consumable.name).all()
    # Har safar ko'rilganda qoldiq tekshiriladi - so'rov o'zi paydo bo'ladi.
    for c in items:
        _check_stock(db, c)
    db.commit()

    rows = [_consumable_out(db, c) for c in items]
    reqs = (db.query(models.PurchaseRequest)
            .filter(models.PurchaseRequest.status == "open").all())
    ids = {c.id for c in items}
    reqs = [r for r in reqs if r.consumable_id in ids]

    return {
        "rows": rows,
        "low_count": sum(1 for r in rows if r["low"]),
        "total_value": round(sum(r["value"] for r in rows), 2),
        "kinds": [{"key": k, "label": lbl, "unit": u}
                  for k, lbl, u in roles.CONSUMABLE_TYPES],
        "reasons": [{"key": k, "label": lbl}
                    for k, lbl in roles.STOCK_MOVE_REASONS],
        "requests": [{
            "id": r.id,
            "consumable_id": r.consumable_id,
            "name": next((c.name for c in items if c.id == r.consumable_id), "—"),
            "qty": r.qty,
            "auto": bool(r.auto),
            "note": r.note,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        } for r in reqs],
        "can_edit": user.role in tuple(roles.INVENTORY_ACCESS),
    }

@router.post("/api/consumables")
def create_consumable(
    payload: schemas.ConsumableCreate,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.INVENTORY_ACCESS)),
):
    if payload.kind not in roles.CONSUMABLE_TYPE_LABELS:
        raise HTTPException(400, "Noto'g'ri mahsulot turi")
    data = payload.model_dump()
    if user.role not in tuple(roles.ORG_WIDE_ROLES) and user.branch_id:
        data["branch_id"] = user.branch_id
    data["unit"] = data.get("unit") or roles.CONSUMABLE_UNITS.get(data["kind"], "dona")
    c = models.Consumable(**data)
    db.add(c); db.commit(); db.refresh(c)
    _check_stock(db, c); db.commit()
    return _consumable_out(db, c)

@router.put("/api/consumables/{cid}")
def update_consumable(
    cid: int,
    payload: schemas.ConsumableUpdate,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.INVENTORY_ACCESS)),
):
    c = db.query(models.Consumable).get(cid)
    if not c:
        raise HTTPException(404, "Mahsulot topilmadi")
    fields = payload.model_dump(exclude_unset=True)
    # Qoldiq qo'lda o'zgartirilmaydi - faqat harakat orqali.
    fields.pop("qty", None)
    for k, v in fields.items():
        setattr(c, k, v)
    db.commit(); db.refresh(c)
    _check_stock(db, c); db.commit()
    return _consumable_out(db, c)

@router.delete("/api/consumables/{cid}")
def delete_consumable(
    cid: int,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.FULL_ACCESS)),
):
    c = db.query(models.Consumable).get(cid)
    if not c:
        raise HTTPException(404, "Mahsulot topilmadi")
    db.query(models.StockMove).filter(
        models.StockMove.consumable_id == cid).delete()
    db.query(models.PurchaseRequest).filter(
        models.PurchaseRequest.consumable_id == cid).delete()
    db.delete(c); db.commit()
    return {"ok": True}

@router.post("/api/consumables/{cid}/move")
def move_stock(
    cid: int,
    payload: schemas.StockMoveCreate,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.INVENTORY_ACCESS)),
):
    """Kirim/chiqim. Qoldiq faqat shu yerdan o'zgaradi - shunda
    "marker qayoqqa ketdi" savoli javobsiz qolmaydi."""
    c = db.query(models.Consumable).get(cid)
    if not c:
        raise HTTPException(404, "Mahsulot topilmadi")
    if payload.reason not in roles.STOCK_MOVE_LABELS:
        raise HTTPException(400, "Noto'g'ri sabab")
    if not payload.qty:
        raise HTTPException(400, "Miqdorni kiriting")

    delta = abs(payload.qty) if payload.reason == "in" else -abs(payload.qty)
    if payload.reason == "correction":
        delta = payload.qty
    if c.qty + delta < 0:
        raise HTTPException(
            400, f"Omborda {c.qty} {c.unit or 'dona'} bor — "
                 f"{abs(delta)} chiqarib bo'lmaydi")

    db.add(models.StockMove(
        consumable_id=cid, delta=delta, reason=payload.reason,
        note=payload.note, created_by=user.full_name))
    c.qty = (c.qty or 0) + delta
    db.commit(); db.refresh(c)
    _check_stock(db, c); db.commit(); db.refresh(c)
    return _consumable_out(db, c)

@router.get("/api/consumables/{cid}/moves")
def list_moves(
    cid: int,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.INVENTORY_VIEW)),
):
    rows = (db.query(models.StockMove)
            .filter(models.StockMove.consumable_id == cid)
            .order_by(models.StockMove.created_at.desc()).limit(100).all())
    return [{
        "id": m.id, "delta": m.delta, "reason": m.reason,
        "reason_label": roles.STOCK_MOVE_LABELS.get(m.reason, m.reason),
        "note": m.note, "by": m.created_by,
        "created_at": m.created_at.isoformat() if m.created_at else None,
    } for m in rows]

@router.post("/api/purchase-requests/{rid}/close")
def close_request(
    rid: int,
    payload: schemas.PurchaseClose,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.INVENTORY_ACCESS)),
):
    """Xarid so'rovini yopish. "received" bo'lsa qoldiq ham to'ldiriladi."""
    pr = db.query(models.PurchaseRequest).get(rid)
    if not pr:
        raise HTTPException(404, "So'rov topilmadi")
    c = db.query(models.Consumable).get(pr.consumable_id)
    if payload.status == "done" and c:
        qty = payload.qty or pr.qty
        db.add(models.StockMove(
            consumable_id=c.id, delta=abs(qty), reason="in",
            note=f"Xarid so'rovi #{pr.id}", created_by=user.full_name))
        c.qty = (c.qty or 0) + abs(qty)
    pr.status = payload.status
    pr.closed_at = datetime.utcnow()
    db.commit()
    return {"ok": True, "qty": c.qty if c else None}

@router.get("/api/books/catalogue")
def books_catalogue(db: Session = Depends(get_db),
                    user=Depends(get_current_user)):
    """Omborda turgan kitoblar — ustoz ro'yxatdan tanlaydi, nomini
    qo'lda yozib xato qilmaydi."""
    q = db.query(models.Consumable).filter(models.Consumable.kind == "book")
    if getattr(user, "branch_id", None):
        q = q.filter(or_(models.Consumable.branch_id == user.branch_id,
                         models.Consumable.branch_id.is_(None)))
    return {"rows": [{
        "id": c.id, "name": c.name, "qty": c.qty,
        "branch_id": c.branch_id,
        "in_stock": (c.qty or 0) > 0,
    } for c in q.order_by(models.Consumable.name).all()]}

@router.get("/api/book-orders")
def book_orders_list(status: str | None = None,
                     db: Session = Depends(get_db),
                     user=Depends(require_role(*roles.BOOK_ORDER_MANAGE))):
    q = db.query(models.BookOrder)
    if user.role == roles.BRANCH_MANAGER and user.branch_id:
        q = q.filter(models.BookOrder.branch_id == user.branch_id)
    if status:
        q = q.filter(models.BookOrder.status == status)
    rows = [_book_out(db, o) for o in
            q.order_by(models.BookOrder.id.desc()).limit(200).all()]
    counts: dict = {}
    for r in rows:
        counts[r["status"]] = counts.get(r["status"], 0) + 1
    return {
        "rows": rows,
        "statuses": [{"key": k, "label": l, "tone": t,
                      "count": counts.get(k, 0)}
                     for k, l, t in roles.BOOK_ORDER_STATUSES],
        "open": sum(1 for r in rows if r["is_open"]),
        "urgent": sum(1 for r in rows
                      if r["is_open"] and r["urgency"] == "urgent"),
        "total_books": sum(r["total_qty"] for r in rows if r["is_open"]),
    }

@router.post("/api/book-orders/{oid}/status")
def book_order_status(oid: int, payload: schemas.BookOrderDecision,
                      db: Session = Depends(get_db),
                      user=Depends(require_role(*roles.BOOK_ORDER_MANAGE))):
    o = db.query(models.BookOrder).get(oid)
    if not o:
        raise HTTPException(404, "Topilmadi")
    if payload.status not in roles.BOOK_STATUS_LABELS:
        raise HTTPException(400, "Noma'lum holat")
    if payload.status == "rejected" and not (payload.note or "").strip():
        raise HTTPException(400, "Rad etish sababini yozing")

    old = o.status
    o.status = payload.status
    o.decided_by = user.id
    o.decided_at = datetime.utcnow()
    o.decision_note = payload.note
    if payload.status == "delivered":
        o.delivered_at = date.today()
        for i in db.query(models.BookOrderItem).filter(
                models.BookOrderItem.order_id == o.id).all():
            i.delivered_qty = i.qty
    # Vazifa ham yopiladi — ikki joyda ikki xil holat qolmasin
    if o.task_id and payload.status in ("delivered", "rejected",
                                        "cancelled"):
        task = db.query(models.Task).get(o.task_id)
        if task:
            task.status = "done" if payload.status == "delivered" \
                else "cancelled"
    db.commit()
    audit.log(db, user, entity="book_order", action="status",
              entity_id=oid, entity_label=o.public_id,
              field="status", old_value=old, new_value=o.status,
              note=payload.note, commit=True)
    return _book_out(db, o)

