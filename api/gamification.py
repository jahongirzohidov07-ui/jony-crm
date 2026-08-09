"""Auto-extracted from main.py during refactor (split-main). Domain: gamification."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import bisect
import json
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

@router.get("/api/coins", response_model=List[schemas.CoinBalance])
def coin_leaderboard(
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.TEACHING_ACCESS)),
):
    """Coin reytingi - kim qancha yig'gan, qanchasini sarflagan."""
    students = scope_to_branch(
        db.query(models.Student), models.Student, user
    ).filter(models.Student.status != "archived").all()
    if not students:
        return []
    ids = [s.id for s in students]

    earned, spent = {}, {}
    rows = db.query(models.CoinEntry).filter(
        models.CoinEntry.student_id.in_(ids)).all()
    for e in rows:
        if e.amount >= 0:
            earned[e.student_id] = earned.get(e.student_id, 0) + e.amount
        else:
            spent[e.student_id] = spent.get(e.student_id, 0) - e.amount

    out = [
        schemas.CoinBalance(
            student_id=s.id, full_name=s.full_name,
            group=s.group.name if s.group else None,
            branch=s.branch.name if s.branch else None,
            earned=earned.get(s.id, 0), spent=spent.get(s.id, 0),
            balance=earned.get(s.id, 0) - spent.get(s.id, 0),
        )
        for s in students
    ]
    out.sort(key=lambda b: -b.balance)
    return out

@router.delete("/api/coins/{entry_id}")
def delete_coin_entry(
    entry_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.COIN_ADMIN)),
):
    """Faqat qo'lda kiritilgan yozuvni o'chirish mumkin - avtomatik
    yozuvlar o'z manbasidan (baho/imtihon) boshqariladi."""
    e = db.query(models.CoinEntry).get(entry_id)
    if not e:
        raise HTTPException(404, "Yozuv topilmadi")
    if e.source != "manual":
        raise HTTPException(
            400,
            "Bu yozuv avtomatik - uni o'zgartirish uchun tegishli bahoni "
            "yoki imtihon natijasini tahrirlang",
        )
    db.delete(e)
    db.commit()
    return {"ok": True}

@router.get("/api/rewards", response_model=List[schemas.RewardOut])
def list_rewards(
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.TEACHING_ACCESS)),
):
    q = scope_to_branch(db.query(models.Reward), models.Reward, user)
    return q.order_by(models.Reward.cost).all()

@router.post("/api/rewards", response_model=schemas.RewardOut)
def create_reward(
    payload: schemas.RewardCreate,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.COIN_ADMIN)),
):
    if payload.cost <= 0:
        raise HTTPException(400, "Coin narxi 0 dan katta bo'lishi kerak")
    r = models.Reward(
        name=payload.name.strip(), cost=payload.cost,
        value_som=payload.value_som, stock=payload.stock,
        active=1 if payload.active else 0,
        branch_id=payload.branch_id if payload.branch_id is not None
        else user.branch_id,
    )
    db.add(r)
    db.commit()
    db.refresh(r)
    return r

@router.put("/api/rewards/{reward_id}", response_model=schemas.RewardOut)
def update_reward(
    reward_id: int,
    payload: schemas.RewardUpdate,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.COIN_ADMIN)),
):
    r = db.query(models.Reward).get(reward_id)
    if not r:
        raise HTTPException(404, "Sovg'a topilmadi")
    data = payload.model_dump(exclude_unset=True)
    if "cost" in data and data["cost"] is not None and data["cost"] <= 0:
        raise HTTPException(400, "Coin narxi 0 dan katta bo'lishi kerak")
    if "active" in data and data["active"] is not None:
        data["active"] = 1 if data["active"] else 0
    for k, v in data.items():
        setattr(r, k, v)
    db.commit()
    db.refresh(r)
    return r

@router.delete("/api/rewards/{reward_id}")
def delete_reward(
    reward_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.COIN_ADMIN)),
):
    r = db.query(models.Reward).get(reward_id)
    if not r:
        raise HTTPException(404, "Sovg'a topilmadi")
    used = db.query(models.RewardRedemption).filter(
        models.RewardRedemption.reward_id == reward_id).count()
    if used:
        # Tarixni buzmaslik uchun o'chirmaymiz, faqat yashiramiz.
        r.active = 0
        db.commit()
        return {"ok": True, "archived": True}
    db.delete(r)
    db.commit()
    return {"ok": True}

@router.post("/api/rewards/redeem", response_model=schemas.RedemptionOut)
def redeem_reward(
    payload: schemas.RedeemRequest,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.TEACHING_ACCESS)),
):
    """Coinni sovg'aga almashtirish. Balans yetmasa rad etiladi."""
    s = db.query(models.Student).get(payload.student_id)
    if not s:
        raise HTTPException(404, "O'quvchi topilmadi")
    r = db.query(models.Reward).get(payload.reward_id)
    if not r or not r.active:
        raise HTTPException(404, "Sovg'a topilmadi")
    if r.stock is not None and r.stock <= 0:
        raise HTTPException(400, "Bu sovg'a tugagan")

    balance = _student_coin_balance(db, s.id)
    if balance < r.cost:
        raise HTTPException(
            400, f"Coin yetarli emas: balans {balance}, kerak {r.cost}")

    red = models.RewardRedemption(student_id=s.id, reward_id=r.id,
                                  coins=r.cost, created_by=user.full_name)
    db.add(red)
    db.flush()
    db.add(models.CoinEntry(student_id=s.id, amount=-r.cost, source="reward",
                            ref_id=red.id, note=r.name,
                            created_by=user.full_name))
    if r.stock is not None:
        r.stock -= 1
    db.commit()
    db.refresh(red)
    return red

@router.delete("/api/rewards/redemptions/{redemption_id}")
def cancel_redemption(
    redemption_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.COIN_ADMIN)),
):
    """Xato berilgan sovg'ani bekor qilish - coin o'quvchiga qaytariladi
    va zaxira tiklanadi."""
    red = db.query(models.RewardRedemption).get(redemption_id)
    if not red:
        raise HTTPException(404, "Yozuv topilmadi")
    _drop_coin_entry(db, "reward", red.id)
    reward = db.query(models.Reward).get(red.reward_id)
    if reward and reward.stock is not None:
        reward.stock += 1
    db.delete(red)
    db.commit()
    return {"ok": True}

@router.get("/api/rewards/redemptions", response_model=List[schemas.RedemptionOut])
def list_redemptions(
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.TEACHING_ACCESS)),
):
    q = db.query(models.RewardRedemption).join(models.Student)
    if user.role not in tuple(roles.ORG_WIDE_ROLES) and user.branch_id:
        q = q.filter(models.Student.branch_id == user.branch_id)
    return q.order_by(models.RewardRedemption.created_at.desc()).limit(200).all()

@router.post("/api/nps")
def add_rating(
    payload: schemas.RatingCreate,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.TEACHING_STAFF)),
):
    t = db.query(models.Teacher).get(payload.teacher_id)
    if not t:
        raise HTTPException(404, "Ustoz topilmadi")
    if not (0 <= payload.score <= 10):
        raise HTTPException(400, "Baho 0 dan 10 gacha bo'lishi kerak")
    if payload.source not in roles.NPS_SOURCE_LABELS:
        raise HTTPException(400, "Noto'g'ri manba")

    s = (db.query(models.Student).get(payload.student_id)
         if payload.student_id else None)
    r = models.TeacherRating(
        teacher_id=t.id, student_id=payload.student_id,
        group_id=s.group_id if s else None,
        source=payload.source, score=payload.score,
        comment=payload.comment,
        period=date.today().isoformat()[:7],
        created_by=user.full_name)
    db.add(r); db.commit()
    return {"id": r.id, "band": roles.nps_band(payload.score)[1]}

@router.get("/api/nps")
def nps_report(
    months: int = 12,
    branch_id: int | None = None,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.NPS_ACCESS)),
):
    """Ustozlar NPS'i. Ustozning o'ziga ham ochiq — lekin o'zining
    bahosi, hamkasbining emas."""
    today = date.today()
    y, m = _shift_month(today.year, today.month, -(max(1, months) - 1))
    start, _e = billing.month_bounds(y, m)
    d0 = _utc_window(start, start)[0]

    teachers = scope_to_branch(db.query(models.Teacher), models.Teacher,
                               user, branch_id).all()
    ids = [t.id for t in teachers]
    rows = (db.query(models.TeacherRating)
            .filter(models.TeacherRating.teacher_id.in_(ids or [-1]),
                    models.TeacherRating.created_at >= d0).all())

    by_t = {}
    for r in rows:
        by_t.setdefault(r.teacher_id, []).append(r)

    out = []
    for t in teachers:
        mine = by_t.get(t.id, [])
        if not mine:
            continue
        scores = [r.score for r in mine]
        pro = sum(1 for s in scores if s >= 9)
        pas = sum(1 for s in scores if 7 <= s <= 8)
        det = sum(1 for s in scores if s <= 6)
        out.append({
            "teacher_id": t.id,
            "full_name": t.full_name,
            "branch": t.branch.name if t.branch else None,
            "answers": len(scores),
            "avg": round(sum(scores) / len(scores), 1),
            "nps": roles.nps_value(scores),
            "promoters": pro,
            "passives": pas,
            "detractors": det,
            "by_student": roles.nps_value(
                [r.score for r in mine if r.source == "student"]),
            "by_parent": roles.nps_value(
                [r.score for r in mine if r.source == "parent"]),
            "comments": [{
                "score": r.score,
                "band": roles.nps_band(r.score)[0],
                "source": roles.NPS_SOURCE_LABELS.get(r.source, r.source),
                "comment": r.comment,
                "date": r.created_at.date().isoformat() if r.created_at else None,
            } for r in sorted(mine, key=lambda x: x.created_at or datetime.min,
                              reverse=True)[:10] if r.comment],
        })
    out.sort(key=lambda r: -r["nps"])

    all_scores = [r.score for r in rows]
    return {
        "months": months,
        "rows": out,
        "overall_nps": roles.nps_value(all_scores),
        "answers": len(all_scores),
        "avg": round(sum(all_scores) / len(all_scores), 1) if all_scores else 0,
        "sources": [{"key": k, "label": lbl} for k, lbl in roles.NPS_SOURCES],
        "bands": [{"key": k, "label": lbl, "tone": t, "min": mn}
                  for mn, k, lbl, t in roles.NPS_BANDS],
        "hint": ("NPS = tarafdorlar foizi − tanqidchilar foizi. "
                 "0 dan yuqori — yaxshi, 50 dan yuqori — a'lo."),
    }

@router.post("/api/referrals")
def add_referral(
    payload: schemas.ReferralCreate,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.DISCOUNT_REQUEST)),
):
    """Kim kimni olib kelganini yozadi. Chegirma keyin — do'sti
    to'lov qilganda — avtomat beriladi."""
    friend = db.query(models.Student).get(payload.student_id)
    inviter = db.query(models.Student).get(payload.referrer_student_id)
    if not friend or not inviter:
        raise HTTPException(404, "O'quvchi topilmadi")
    if friend.id == inviter.id:
        raise HTTPException(400, "O'zini o'zi olib kela olmaydi")

    exists = (db.query(models.Discount)
              .filter(models.Discount.kind == "referral",
                      models.Discount.student_id == inviter.id,
                      models.Discount.referrer_student_id == friend.id)
              .first())
    if exists:
        raise HTTPException(400, "Bu referral allaqachon yozilgan")

    # Do'sti allaqachon to'lov qilganmi
    paid = (db.query(func.sum(models.Payment.amount))
            .filter(models.Payment.student_id == friend.id,
                    models.Payment.kind == "payment").scalar() or 0)

    d = models.Discount(
        student_id=inviter.id,
        kind="referral",
        percent=roles.REFERRAL_PERCENT,
        reason=f"{friend.full_name} ni olib keldi",
        start_date=date.today(),
        end_date=date.today() + timedelta(days=30 * roles.REFERRAL_MONTHS),
        referrer_student_id=friend.id,
        requested_by=user.full_name,
        status="active" if paid >= roles.REFERRAL_MIN_PAYMENT else "pending",
    )
    if d.status == "active":
        d.approved_by = "Tizim (do'sti to'lov qildi)"
        d.approved_at = datetime.utcnow()
    db.add(d); db.commit(); db.refresh(d)
    return {
        "id": d.id,
        "status": d.status,
        "message": ("Chegirma darrov berildi — do'sti allaqachon to'lagan"
                    if d.status == "active"
                    else "Do'sti to'lov qilgach chegirma avtomat beriladi"),
    }

@router.get("/api/referrals")
def referral_report(
    months: int = 12,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.MARKETING_ANALYTICS)),
):
    """Referral dasturi qancha ishlayapti: kim ko'p olib kelgan,
    qancha chegirma berildi va bu qancha pul keltirdi."""
    today = date.today()
    y, m = _shift_month(today.year, today.month, -(max(1, months) - 1))
    start, _e = billing.month_bounds(y, m)

    rows = (db.query(models.Discount)
            .filter(models.Discount.kind == "referral",
                    models.Discount.created_at >= datetime.combine(
                        start, datetime.min.time())).all())
    students = {s.id: s for s in db.query(models.Student).all()}
    paid = _student_payments(db)

    by_inviter = {}
    for d in rows:
        inv = students.get(d.student_id)
        fr = students.get(d.referrer_student_id) if d.referrer_student_id else None
        if not inv:
            continue
        r = by_inviter.setdefault(inv.id, {
            "student_id": inv.id, "full_name": inv.full_name,
            "invited": 0, "active": 0, "friends": [],
            "revenue_brought": 0.0, "discount_given": 0.0,
        })
        r["invited"] += 1
        if d.status == "active":
            r["active"] += 1
            fee = inv.group.monthly_fee if inv.group else 0
            r["discount_given"] += (fee or 0) * (d.percent or 0) / 100
        if fr:
            r["friends"].append({
                "id": fr.id, "name": fr.full_name,
                "status": fr.status,
                "paid": round(paid.get(fr.id, {}).get("total", 0.0), 2),
            })
            r["revenue_brought"] += paid.get(fr.id, {}).get("total", 0.0)

    out = sorted(by_inviter.values(), key=lambda r: -r["revenue_brought"])
    for r in out:
        r["revenue_brought"] = round(r["revenue_brought"], 2)
        r["discount_given"] = round(r["discount_given"], 2)
        r["net"] = round(r["revenue_brought"] - r["discount_given"], 2)

    total_rev = sum(r["revenue_brought"] for r in out)
    total_disc = sum(r["discount_given"] for r in out)
    return {
        "months": months,
        "rows": out,
        "inviters": len(out),
        "invited": sum(r["invited"] for r in out),
        "active": sum(r["active"] for r in out),
        "pending": sum(1 for d in rows if d.status == "pending"),
        "revenue": round(total_rev, 2),
        "discount": round(total_disc, 2),
        "net": round(total_rev - total_disc, 2),
        "percent": roles.REFERRAL_PERCENT,
        "months_valid": roles.REFERRAL_MONTHS,
        "hint": (f"Do'stini olib kelgan o'quvchi {roles.REFERRAL_PERCENT}% "
                 f"chegirma oladi. Chegirma do'sti TO'LOV QILGANDA "
                 f"avtomat yoqiladi — shunchaki ro'yxatdan o'tgani "
                 f"yetarli emas."),
    }

@router.get("/api/rewards/requests")
def reward_requests(
    status_filter: str = "requested",
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.REWARD_GIVE)),
):
    """O'quvchilar so'ragan sovg'alar — kimga nima berish kerak."""
    q = db.query(models.RewardRedemption)
    if status_filter:
        q = q.filter(models.RewardRedemption.status == status_filter)
    rows = q.order_by(models.RewardRedemption.created_at).all()

    allowed = {x.id for x in scope_to_branch(
        db.query(models.Student), models.Student, user).all()}
    rows = [r for r in rows if r.student_id in allowed]

    return {
        "rows": [{
            "id": r.id,
            "student_id": r.student_id,
            "student": r.student.full_name if r.student else "—",
            "group": (r.student.group.name
                      if r.student and r.student.group else None),
            "reward": r.reward.name if r.reward else "—",
            "coins": r.coins,
            "status": r.status or "given",
            "status_label": roles.REDEEM_STATUS_LABELS.get(
                r.status or "given", r.status),
            "tone": roles.REDEEM_STATUS_TONE.get(r.status or "given", "slate"),
            "by_student": bool(r.requested_by_student),
            "date": r.created_at.date().isoformat() if r.created_at else None,
            "given_by": r.given_by,
        } for r in rows],
        "count": len(rows),
        "statuses": [{"key": k, "label": lbl, "tone": t}
                     for k, lbl, t in roles.REDEEM_STATUSES],
    }

@router.post("/api/rewards/requests/{rid}/give")
def give_reward(
    rid: int,
    payload: schemas.RewardDecision,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.REWARD_GIVE)),
):
    """Sovg'ani qo'lga berish yoki rad etish.

    BERILDI — coin hisobdan yechiladi (shu paytgacha faqat band edi).
    RAD ETILDI — coin qaytadi."""
    red = db.query(models.RewardRedemption).get(rid)
    if not red:
        raise HTTPException(404, "So'rov topilmadi")
    if red.status != "requested":
        raise HTTPException(400, "Bu so'rov allaqachon hal qilingan")

    r = db.query(models.Reward).get(red.reward_id)
    s = db.query(models.Student).get(red.student_id)

    if not payload.give:
        red.status = "rejected"
        red.note = payload.note
        red.given_by = user.full_name
        red.given_at = datetime.utcnow()
        db.commit()
        return {"ok": True, "status": "rejected"}

    # Berilganda coin yechiladi
    balance = _student_coin_balance(db, red.student_id)
    if balance < red.coins:
        raise HTTPException(
            400, f"Coin yetmayapti: balans {balance}, kerak {red.coins}")

    db.add(models.CoinEntry(
        student_id=red.student_id, amount=-red.coins, source="reward",
        ref_id=red.id, note=r.name if r else "Sovg'a",
        created_by=user.full_name))
    red.status = "given"
    red.given_by = user.full_name
    red.given_at = datetime.utcnow()
    red.note = payload.note
    if r and r.stock is not None:
        r.stock -= 1
    db.commit()

    audit.log(db, user, entity="reward", action="update", entity_id=red.id,
              entity_label=s.full_name if s else "—",
              field="Sovg'a berildi",
              new_value=f"{r.name if r else ''} ({red.coins} coin)",
              branch_id=s.branch_id if s else None, commit=True)
    return {"ok": True, "status": "given",
            "balance": _student_coin_balance(db, red.student_id)}

def _seed_gamification(db: Session) -> None:
    """Ligalar va qoidalar bazaga bir marta tushadi. Admin o'zgartirsa
    — qayta yozilmaydi, faqat YETISHMAYOTGANI qo'shiladi."""
    have = {r.key for r in db.query(models.XpLeague).all()}
    added = False
    for rank, key, name, lo, hi, color, icon, coin in roles.XP_LEAGUES:
        if key in have:
            continue
        db.add(models.XpLeague(
            key=key, name=name, rank=rank, minimum_xp=lo, maximum_xp=hi,
            color=color, icon=icon, reward_coin=coin, is_active=1))
        added = True
    if added:
        db.commit()

    have = {r.event_code for r in db.query(models.XpRule).all()}
    added = False
    for (code, name, cat, xp, coin, per_lesson, per_day, per_week,
         per_month, mode, approval) in roles.XP_RULES:
        if code in have:
            continue
        db.add(models.XpRule(
            event_code=code, name=name, category=cat, default_xp=xp,
            default_coin=coin, maximum_per_lesson=per_lesson,
            maximum_per_day=per_day, maximum_per_week=per_week,
            maximum_per_month=per_month, mode=mode,
            requires_approval=1 if approval else 0, is_active=1))
        added = True
    if added:
        db.commit()

def reverse_xp(db: Session, tx_id: int, *, by_user: models.User,
               reason: str) -> dict:
    """Xato XP'ni qaytaradi. Asl yozuv O'CHIRILMAYDI — manfiy yozuv
    qo'shiladi, shunda tarix to'liq qoladi."""
    tx = db.query(models.XpTransaction).get(tx_id)
    if not tx:
        raise HTTPException(404, "Tranzaksiya topilmadi")
    if tx.is_reversal:
        raise HTTPException(400, "Bekor qilingan yozuvni qayta bekor "
                                 "qilib bo'lmaydi")
    already = (db.query(models.XpTransaction)
               .filter(models.XpTransaction.reversed_transaction_id == tx.id)
               .first())
    if already:
        raise HTTPException(400, "Bu yozuv allaqachon bekor qilingan")

    rev = models.XpTransaction(
        student_id=tx.student_id, amount=-(tx.amount or 0),
        category=tx.category, event_code="REVERSAL",
        source_type="reversal", group_id=tx.group_id,
        branch_id=tx.branch_id, lesson_id=tx.lesson_id,
        exam_id=tx.exam_id, season_id=tx.season_id,
        awarded_by_user_id=by_user.id, reason=reason,
        reversed_transaction_id=tx.id, is_reversal=1)
    db.add(rev)
    db.flush()
    _recalc_gamification(db, tx.student_id, commit=False)
    audit.log(db, by_user, entity="xp", action="update", entity_id=tx.id,
              entity_label=f"{tx.event_code} {tx.amount}",
              note=f"Bekor qilindi: {reason}", branch_id=tx.branch_id)
    db.commit()
    return {"ok": True, "reversal_id": rev.id, "amount": -(tx.amount or 0)}

def _rule_out(r) -> dict:
    return {
        "id": r.id, "event_code": r.event_code, "name": r.name,
        "description": r.description, "category": r.category,
        "category_label": roles.XP_CATEGORY_LABELS.get(r.category,
                                                       r.category),
        "tone": roles.XP_CATEGORY_TONE.get(r.category, "slate"),
        "default_xp": r.default_xp or 0, "default_coin": r.default_coin or 0,
        "maximum_per_lesson": r.maximum_per_lesson,
        "maximum_per_day": r.maximum_per_day,
        "maximum_per_week": r.maximum_per_week,
        "maximum_per_month": r.maximum_per_month,
        "mode": r.mode, "requires_approval": bool(r.requires_approval),
        "allowed_roles": r.allowed_roles,
        "is_active": bool(r.is_active),
    }

@router.get("/api/gamification/leagues")
def list_leagues(
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.XP_VIEW)),
):
    _seed_gamification(db)
    counts: dict = {}
    for g in db.query(models.StudentGamification).all():
        if g.current_league_id:
            counts[g.current_league_id] = counts.get(g.current_league_id, 0) + 1
    return {
        "rows": [_league_out(lg, counts.get(lg.id, 0))
                 for lg in db.query(models.XpLeague)
                 .order_by(models.XpLeague.rank).all()],
        "xp_per_level": roles.XP_PER_LEVEL,
        "can_edit": user.role in roles.XP_ADMIN,
    }

@router.put("/api/gamification/leagues/{lid}")
def update_league(
    lid: int,
    payload: schemas.LeagueUpdate,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.XP_ADMIN)),
):
    lg = db.query(models.XpLeague).get(lid)
    if not lg:
        raise HTTPException(404, "Liga topilmadi")
    given = payload.model_dump(exclude_unset=True)
    before = {k: getattr(lg, k) for k in given}
    for k, v in given.items():
        setattr(lg, k, int(v) if k == "is_active" and v is not None else v)
    db.commit()
    audit.log(db, user, entity="league", action="update", entity_id=lg.id,
              entity_label=lg.name, old_value=str(before),
              new_value=str(given), note="Liga o'zgartirildi")

    # Chegara o'zgarsa hamma o'quvchining ligasi qayta hisoblanadi
    touched = 0
    if "minimum_xp" in given or "maximum_xp" in given:
        for g in db.query(models.StudentGamification).all():
            _recalc_gamification(db, g.student_id, commit=False)
            touched += 1
        db.commit()
    return {"ok": True, "recalculated": touched}

@router.get("/api/gamification/rules")
def list_xp_rules(
    category: str | None = None,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.XP_VIEW)),
):
    _seed_gamification(db)
    q = db.query(models.XpRule)
    if category:
        q = q.filter(models.XpRule.category == category)
    rows = q.order_by(models.XpRule.category, models.XpRule.id).all()
    return {
        "rows": [_rule_out(r) for r in rows],
        "categories": [{"key": k, "label": lbl, "tone": t}
                       for k, lbl, t in roles.XP_CATEGORIES],
        "quick": roles.TEACHER_QUICK_XP,
        "teacher_week_limit": roles.TEACHER_XP_PER_WEEK,
        "teacher_lesson_limit": roles.TEACHER_XP_PER_LESSON,
        "approval_above": roles.APPROVAL_ABOVE_XP,
        "can_edit": user.role in roles.XP_ADMIN,
    }

@router.put("/api/gamification/rules/{rid}")
def update_xp_rule(
    rid: int,
    payload: schemas.XpRuleUpdate,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.XP_ADMIN)),
):
    """Qoidani tahrirlash. Qiymat o'zgarsa ESKI tranzaksiyalar
    o'zgarmaydi — ular o'sha paytdagi qiymat bilan yozilgan."""
    r = db.query(models.XpRule).get(rid)
    if not r:
        raise HTTPException(404, "Qoida topilmadi")
    given = payload.model_dump(exclude_unset=True)
    before = {k: getattr(r, k) for k in given}
    for k, v in given.items():
        if k in ("requires_approval", "is_active"):
            v = 1 if v else 0
        setattr(r, k, v)
    db.commit()
    audit.log(db, user, entity="xp_rule", action="update", entity_id=r.id,
              entity_label=r.event_code, old_value=str(before),
              new_value=str(given), note="XP qoidasi o'zgartirildi")
    db.commit()
    return {"ok": True}

@router.get("/api/gamification/seasons")
def list_seasons(
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.XP_VIEW)),
):
    rows = (db.query(models.XpSeason)
            .order_by(models.XpSeason.start_date.desc()).all())
    cur = _active_season(db)
    return {
        "rows": [{
            "id": s.id, "name": s.name,
            "start_date": s.start_date.isoformat() if s.start_date else None,
            "end_date": s.end_date.isoformat() if s.end_date else None,
            "is_active": bool(s.is_active),
            "current": bool(cur and cur.id == s.id),
            "note": s.note,
        } for s in rows],
        "current": cur.name if cur else None,
        "hint": ("Mavsum XP yangi mavsumda 0 dan boshlanadi. "
                 "Umumiy XP hech qachon reset qilinmaydi."),
        "can_edit": user.role in roles.XP_ADMIN,
    }

@router.post("/api/gamification/seasons")
def create_season(
    payload: schemas.SeasonCreate,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.XP_ADMIN)),
):
    for s in db.query(models.XpSeason).filter(
            models.XpSeason.is_active == 1).all():
        s.is_active = 0
        if not s.end_date:
            s.end_date = date.today()
    row = models.XpSeason(
        name=payload.name, start_date=payload.start_date or date.today(),
        end_date=payload.end_date, note=payload.note, is_active=1,
        created_by=user.full_name)
    db.add(row)
    db.commit()
    for g in db.query(models.StudentGamification).all():
        _recalc_gamification(db, g.student_id, commit=False)
    db.commit()
    audit.log(db, user, entity="season", action="create", entity_id=row.id,
              entity_label=row.name, note="Yangi mavsum ochildi")
    db.commit()
    return {"ok": True, "id": row.id}

def _teacher_manual_used(db: Session, student_id: int, by_user_id: int,
                         since: date, lesson_id: int | None = None) -> float:
    q = (db.query(func.coalesce(func.sum(models.XpTransaction.amount), 0))
         .filter(models.XpTransaction.student_id == student_id,
                 models.XpTransaction.awarded_by_user_id == by_user_id,
                 models.XpTransaction.source_type == "manual",
                 models.XpTransaction.is_reversal == 0,
                 models.XpTransaction.created_at
                 >= datetime.combine(since, datetime.min.time())))
    if lesson_id:
        q = q.filter(models.XpTransaction.lesson_id == lesson_id)
    return float(q.scalar() or 0)

def _can_award(db: Session, user: models.User, student: models.Student,
               rule: models.XpRule, amount: float,
               lesson_id: int | None) -> str | None:
    """Ustoz chegaradan chiqmaganini tekshiradi. Sabab qaytsa — bermaymiz."""
    if user.role in roles.XP_ADMIN:
        return None
    if user.role not in (roles.TEACHER, roles.SUPPORT_TEACHER,
                         roles.HEAD_SUPPORT):
        return None

    # Faqat o'z guruhidagi o'quvchiga
    mine = _teacher_of_user(db, user)
    gids = {g.id for g in db.query(models.Group)
            .filter(models.Group.teacher_id == mine.id).all()} if mine else set()
    if student.group_id not in gids:
        _fraud_alert(db, "foreign_group", student_id=student.id,
                     user_id=user.id,
                     description=(f"{user.full_name} o'ziga biriktirilmagan "
                                  f"guruhga XP berishga urindi"))
        db.commit()
        return "Faqat o'z guruhingizdagi o'quvchiga XP bera olasiz"

    if rule.event_code not in roles.TEACHER_QUICK_XP:
        return "Bu qoidadan XP berish sizga ochiq emas"

    week_start = date.today() - timedelta(days=date.today().weekday())
    used_week = _teacher_manual_used(db, student.id, user.id, week_start)
    if used_week + amount > roles.TEACHER_XP_PER_WEEK:
        return (f"Haftalik chegara: bitta o'quvchiga {roles.TEACHER_XP_PER_WEEK} "
                f"XP (bu hafta {round(used_week)} berilgan)")
    if lesson_id:
        used_lesson = _teacher_manual_used(db, student.id, user.id,
                                           date.today(), lesson_id)
        if used_lesson + amount > roles.TEACHER_XP_PER_LESSON:
            return (f"Bir darsda ko'pi bilan {roles.TEACHER_XP_PER_LESSON} XP "
                    f"berish mumkin (bu darsda {round(used_lesson)} berilgan)")
    return None

@router.post("/api/gamification/award")
def give_xp(
    payload: schemas.XpAward,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.XP_AWARD)),
):
    """Qo'lda XP berish. Ustoz o'zi miqdor yozolmaydi — faqat mavjud
    qoidadan va chegara doirasida."""
    s = db.query(models.Student).get(payload.student_id)
    if not s:
        raise HTTPException(404, "O'quvchi topilmadi")
    rule = _xp_rule(db, payload.event_code)
    if not rule:
        raise HTTPException(400, "Bunday XP qoidasi yo'q")

    # Ustoz miqdorni o'zgartira olmaydi
    amount = rule.default_xp or 0
    if payload.amount is not None and user.role in roles.XP_ADMIN:
        amount = payload.amount

    blocked = _can_award(db, user, s, rule, amount, payload.lesson_id)
    if blocked:
        raise HTTPException(400, blocked)

    # Katta miqdor — tasdiqqa
    if (rule.requires_approval or amount > roles.APPROVAL_ABOVE_XP) \
            and user.role not in roles.FULL_ACCESS:
        if not (payload.reason or "").strip():
            raise HTTPException(400, "Sabab yozing")
        req = models.XpApprovalRequest(
            student_id=s.id, event_code=payload.event_code, amount=amount,
            reason=payload.reason, requested_by=user.id, status="pending")
        db.add(req)
        db.commit()
        return {"ok": True, "pending": True, "request_id": req.id,
                "message": "Tasdiqqa yuborildi"}

    if user.role in roles.XP_ADMIN and not (payload.reason or "").strip() \
            and amount > roles.APPROVAL_ABOVE_XP:
        raise HTTPException(400, "Katta XP uchun sabab yozish shart")

    res = award_xp(db, student_id=s.id, event_code=payload.event_code,
                   amount=amount, by_user=user, reason=payload.reason,
                   lesson_id=payload.lesson_id, source_type="manual")
    if not res.get("ok"):
        raise HTTPException(400, res.get("reason", "XP berilmadi"))

    if amount > roles.APPROVAL_ABOVE_XP:
        _fraud_alert(db, "big_manual", student_id=s.id, user_id=user.id,
                     transaction_id=res["transaction_id"],
                     description=(f"{user.full_name} {amount} XP berdi: "
                                  f"{payload.reason or 'sababsiz'}"))
        db.commit()
    return res

@router.post("/api/gamification/award-bulk")
def give_xp_bulk(
    payload: schemas.XpBulkAward,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.XP_AWARD)),
):
    """Butun guruhga bir vaqtda XP. Kimga berilgani va kimga
    berilmagani aniq qaytadi."""
    rule = _xp_rule(db, payload.event_code)
    if not rule:
        raise HTTPException(400, "Bunday XP qoidasi yo'q")
    amount = rule.default_xp or 0

    given, skipped = [], []
    for sid in payload.student_ids:
        s = db.query(models.Student).get(sid)
        if not s:
            continue
        blocked = _can_award(db, user, s, rule, amount, payload.lesson_id)
        if blocked:
            skipped.append({"student_id": sid, "full_name": s.full_name,
                            "reason": blocked})
            continue
        res = award_xp(db, student_id=sid, event_code=payload.event_code,
                       amount=amount, by_user=user, reason=payload.reason,
                       lesson_id=payload.lesson_id, source_type="manual")
        if res.get("ok"):
            given.append({"student_id": sid, "full_name": s.full_name})
        else:
            skipped.append({"student_id": sid, "full_name": s.full_name,
                            "reason": res.get("reason", "—")})

    if len(given) >= roles.MASS_AWARD_STUDENTS and amount > 20:
        _fraud_alert(db, "mass_award", user_id=user.id,
                     description=(f"{user.full_name} {len(given)} o'quvchiga "
                                  f"{amount} XP dan berdi"))
        db.commit()
    return {"given": given, "skipped": skipped,
            "total_xp": round(len(given) * amount, 1),
            "rule": rule.name, "amount": amount}

@router.post("/api/gamification/transactions/{tx_id}/reverse")
def reverse_transaction(
    tx_id: int,
    payload: schemas.XpReverse,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.XP_ADMIN)),
):
    if not (payload.reason or "").strip():
        raise HTTPException(400, "Bekor qilish sababini yozing")
    return reverse_xp(db, tx_id, by_user=user, reason=payload.reason)

@router.post("/api/gamification/certificate")
def award_certificate(
    payload: schemas.CertAward,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.XP_ADMIN)),
):
    """Sertifikat XP'si. Bir raqamga ikki marta berilmaydi; yangi
    yuqoriroq natijada standart holatda faqat FARQI beriladi."""
    res = _xp_for_certificate(
        db, payload.student_id, kind=payload.kind,
        code=payload.event_code, cert_no=payload.cert_no, by_user=user,
        mode=payload.mode or roles.CERT_MODE_DIFF, reason=payload.reason)
    if not res.get("ok"):
        raise HTTPException(400, res.get("reason", "XP berilmadi"))
    return res

@router.get("/api/gamification/approvals")
def list_approvals(
    status_filter: str = "pending",
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.XP_ADMIN)),
):
    q = db.query(models.XpApprovalRequest)
    if status_filter:
        q = q.filter(models.XpApprovalRequest.status == status_filter)
    rows = q.order_by(models.XpApprovalRequest.created_at.desc()).limit(200).all()
    users = {u.id: u.full_name for u in db.query(models.User).all()}
    return {"rows": [{
        "id": r.id, "student_id": r.student_id,
        "student": r.student.full_name if r.student else None,
        "event_code": r.event_code, "amount": r.amount,
        "reason": r.reason, "status": r.status,
        "requested_by": users.get(r.requested_by),
        "created_at": r.created_at.isoformat() if r.created_at else None,
    } for r in rows]}

@router.post("/api/gamification/approvals/{rid}")
def decide_approval(
    rid: int,
    payload: schemas.ApprovalDecision,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.XP_ADMIN)),
):
    r = db.query(models.XpApprovalRequest).get(rid)
    if not r:
        raise HTTPException(404, "So'rov topilmadi")
    if r.status != "pending":
        raise HTTPException(400, "Bu so'rov allaqachon hal qilingan")
    r.status = "approved" if payload.approve else "rejected"
    r.decided_by = user.id
    r.decided_at = datetime.utcnow()
    r.decision_note = payload.note
    db.commit()
    if payload.approve:
        res = award_xp(db, student_id=r.student_id, event_code=r.event_code,
                       amount=r.amount, by_user=user, reason=r.reason,
                       source_type="manual")
        return {"ok": True, "awarded": res}
    return {"ok": True, "awarded": None}

def _mask_name(full: str) -> str:
    """Ommaviy leaderboardda maxfiylik: Jahongir Z."""
    parts = (full or "").split()
    if len(parts) < 2:
        return full
    return f"{parts[0]} {parts[1][0]}."

@router.get("/api/gamification/leaderboard")
def leaderboard(
    scope: str = "lifetime",
    branch_id: int | None = None,
    group_id: int | None = None,
    league: str | None = None,
    limit: int = 50,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """Reyting. O'quvchi va ota-ona ismlarni qisqartirilgan ko'radi."""
    today = date.today()
    since = None
    if scope == "week":
        since = today - timedelta(days=today.weekday())
    elif scope == "month":
        since, _e = billing.month_bounds(today.year, today.month)

    # Xonalardagi o'quvchilar soni FAQAT FAOLLARDAN olinadi
    students = scope_to_branch(db.query(models.Student), models.Student,
                               user, branch_id).filter(
        models.Student.status == "active").all()
    if group_id:
        students = [s for s in students if s.group_id == group_id]
    ids = [s.id for s in students]
    if not ids:
        return {"rows": [], "scope": scope, "scopes": [
            {"key": k, "label": lbl} for k, lbl in roles.LEADERBOARD_SCOPES]}

    gam = {g.student_id: g for g in db.query(models.StudentGamification)
           .filter(models.StudentGamification.student_id.in_(ids)).all()}
    lgs = {l.id: l for l in db.query(models.XpLeague).all()}

    period_xp: dict = {}
    if since:
        for t in (db.query(models.XpTransaction)
                  .filter(models.XpTransaction.student_id.in_(ids),
                          models.XpTransaction.created_at
                          >= datetime.combine(since, datetime.min.time()))
                  .all()):
            period_xp[t.student_id] = period_xp.get(t.student_id, 0) + (t.amount or 0)

    by_cat_cache: dict = {}
    rows = []
    for s in students:
        g = gam.get(s.id)
        lg = lgs.get(g.current_league_id) if g and g.current_league_id else None
        if league and (not lg or lg.key != league):
            continue
        if scope == "season":
            xp = g.season_xp if g else 0
        elif since:
            xp = period_xp.get(s.id, 0)
        else:
            xp = g.lifetime_xp if g else 0
        cats = json.loads(g.by_category) if g and g.by_category else {}
        by_cat_cache[s.id] = cats
        rows.append({
            "student_id": s.id,
            "full_name": s.full_name,
            "group": s.group.name if s.group else None,
            "branch": s.branch.name if s.branch else None,
            "league": lg.name if lg else None,
            "league_icon": lg.icon if lg else None,
            "league_color": lg.color if lg else None,
            "level": g.current_level if g else 1,
            "xp": round(xp or 0, 1),
            "lifetime_xp": round((g.lifetime_xp if g else 0) or 0, 1),
            "academic_xp": round(cats.get("academic", 0), 1),
        })

    # Tie-breaker: XP -> akademik XP -> ismi
    rows.sort(key=lambda r: (-r["xp"], -r["academic_xp"], r["full_name"]))
    rows = rows[:max(1, min(limit, 300))]

    # Oldingi kunning snapshoti bilan solishtiramiz
    prev = {sn.student_id: sn.rank for sn in
            db.query(models.SeasonRankSnapshot)
            .filter(models.SeasonRankSnapshot.scope == scope,
                    models.SeasonRankSnapshot.taken_on < today)
            .order_by(models.SeasonRankSnapshot.taken_on.desc())
            .limit(500).all()}

    public = user.role in (roles.STUDENT, roles.PARENT)
    for i, r in enumerate(rows, 1):
        r["rank"] = i
        old = prev.get(r["student_id"])
        r["change"] = (None if old is None else old - i)
        r["is_new"] = old is None
        if public:
            r["full_name"] = _mask_name(r["full_name"])

    # Bugungi snapshotni saqlaymiz - ertaga o'zgarish ko'rinsin
    if not db.query(models.SeasonRankSnapshot).filter(
            models.SeasonRankSnapshot.scope == scope,
            models.SeasonRankSnapshot.taken_on == today).first():
        for r in rows:
            db.add(models.SeasonRankSnapshot(
                scope=scope, student_id=r["student_id"], rank=r["rank"],
                xp=r["xp"], taken_on=today))
        db.commit()

    return {
        "rows": rows, "scope": scope,
        "scopes": [{"key": k, "label": lbl}
                   for k, lbl in roles.LEADERBOARD_SCOPES],
        "leagues": [{"key": l.key, "name": l.name, "icon": l.icon}
                    for l in _leagues(db)],
        "masked": public,
    }

@router.get("/api/gamification/overview")
def gamification_overview(
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.XP_ADMIN)),
):
    today = date.today()
    w_start = today - timedelta(days=today.weekday())

    def total(since=None, manual=None):
        q = db.query(func.coalesce(func.sum(models.XpTransaction.amount), 0))
        if since:
            q = q.filter(models.XpTransaction.created_at
                         >= datetime.combine(since, datetime.min.time()))
        if manual is not None:
            q = (q.filter(models.XpTransaction.source_type == "manual")
                 if manual else
                 q.filter(models.XpTransaction.source_type != "manual"))
        return round(float(q.scalar() or 0), 1)

    all_tx = db.query(models.XpTransaction).all()
    manual = sum(t.amount or 0 for t in all_tx if t.source_type == "manual")
    auto = sum(t.amount or 0 for t in all_tx if t.source_type != "manual")
    grand = manual + auto

    codes: dict = {}
    for t in all_tx:
        if t.event_code:
            codes[t.event_code] = codes.get(t.event_code, 0) + 1
    top_code = max(codes.items(), key=lambda x: x[1])[0] if codes else None
    rules = {r.event_code: r.name for r in db.query(models.XpRule).all()}

    gam = db.query(models.StudentGamification).all()
    active = [g for g in gam if (g.lifetime_xp or 0) > 0]
    lgs = {l.id: l for l in db.query(models.XpLeague).all()}
    dist: dict = {}
    for g in gam:
        if g.current_league_id in lgs:
            k = lgs[g.current_league_id].name
            dist[k] = dist.get(k, 0) + 1

    # Haftada kamida 1 XP olganlar
    got_week = {t.student_id for t in all_tx
                if t.created_at and t.created_at.date() >= w_start}
    students = db.query(models.Student).filter(
        models.Student.status.in_(["active", "trial"])).all()
    silent = []
    for s in students:
        last = max((t.created_at for t in all_tx if t.student_id == s.id),
                   default=None)
        if not last or (datetime.utcnow() - last).days >= 14:
            silent.append(s.full_name)

    season = _active_season(db)
    open_alerts = db.query(models.XpFraudAlert).filter(
        models.XpFraudAlert.status == "open").count()

    return {
        "today": total(today),
        "week": total(w_start),
        "total": round(grand, 1),
        "active_students": len(active),
        "avg_per_student": (round(sum(g.lifetime_xp or 0 for g in active)
                                  / len(active), 1) if active else 0),
        "top_event": rules.get(top_code or "", top_code),
        "manual_percent": (round(manual / grand * 100, 1) if grand else 0),
        "auto_percent": (round(auto / grand * 100, 1) if grand else 0),
        "season": season.name if season else None,
        "season_participants": len([g for g in gam if (g.season_xp or 0) > 0]),
        "league_distribution": [{"league": k, "students": v}
                                for k, v in sorted(dist.items(),
                                                   key=lambda x: -x[1])],
        "weekly_active_percent": (round(len(got_week) / len(students) * 100, 1)
                                  if students else 0),
        "silent_14d": len(silent),
        "silent_names": silent[:15],
        "open_alerts": open_alerts,
    }

@router.get("/api/gamification/transactions")
def list_transactions(
    student_id: int | None = None,
    event_code: str | None = None,
    source_type: str | None = None,
    branch_id: int | None = None,
    limit: int = 200,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.XP_VIEW)),
):
    q = db.query(models.XpTransaction)
    if student_id:
        q = q.filter(models.XpTransaction.student_id == student_id)
    if event_code:
        q = q.filter(models.XpTransaction.event_code == event_code)
    if source_type:
        q = q.filter(models.XpTransaction.source_type == source_type)
    if branch_id:
        q = q.filter(models.XpTransaction.branch_id == branch_id)
    rows = (q.order_by(models.XpTransaction.created_at.desc())
            .limit(max(1, min(limit, 1000))).all())

    names = {s.id: s.full_name for s in db.query(models.Student).all()}
    users = {u.id: u.full_name for u in db.query(models.User).all()}
    rules = {r.event_code: r.name for r in db.query(models.XpRule).all()}
    return {"rows": [{
        "id": t.id, "student_id": t.student_id,
        "student": names.get(t.student_id),
        "amount": round(t.amount or 0, 1),
        "event_code": t.event_code,
        "label": rules.get(t.event_code or "",
                           "Bekor qilindi" if t.is_reversal else t.event_code),
        "category": t.category,
        "category_label": roles.XP_CATEGORY_LABELS.get(t.category or "", "—"),
        "source_type": t.source_type,
        "source_label": roles.XP_SOURCE_LABELS.get(t.source_type or "", "—"),
        "by": users.get(t.awarded_by_user_id) or "Tizim",
        "reason": t.reason,
        "is_reversal": bool(t.is_reversal),
        "reversed_id": t.reversed_transaction_id,
        "date": t.created_at.isoformat() if t.created_at else None,
    } for t in rows],
        "can_reverse": user.role in roles.XP_ADMIN}

@router.post("/api/gamification/recalculate")
def recalculate_all(
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.XP_ADMIN)),
):
    """Jamlanmani jurnaldan qayta hisoblaydi. Jurnal — haqiqat manbai,
    shuning uchun bu amal hech qachon ma'lumot yo'qotmaydi."""
    ids = {t.student_id for t in db.query(models.XpTransaction).all()}
    for sid in ids:
        _recalc_gamification(db, sid, commit=False)
    db.commit()
    audit.log(db, user, entity="xp", action="update",
              note=f"{len(ids)} o'quvchining XP jamlanmasi qayta hisoblandi")
    db.commit()
    return {"ok": True, "students": len(ids)}

@router.get("/api/gamification/fraud")
def list_fraud(
    status_filter: str = "open",
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.XP_ADMIN)),
):
    q = db.query(models.XpFraudAlert)
    if status_filter:
        q = q.filter(models.XpFraudAlert.status == status_filter)
    rows = q.order_by(models.XpFraudAlert.created_at.desc()).limit(200).all()
    names = {s.id: s.full_name for s in db.query(models.Student).all()}
    users = {u.id: u.full_name for u in db.query(models.User).all()}
    counts: dict = {}
    for a in db.query(models.XpFraudAlert).all():
        counts[a.status] = counts.get(a.status, 0) + 1
    return {"rows": [{
        "id": a.id, "alert_type": a.alert_type,
        "label": roles.FRAUD_LABELS.get(a.alert_type, a.alert_type),
        "severity": a.severity,
        "tone": roles.FRAUD_TONE.get(a.severity, "slate"),
        "student": names.get(a.student_id),
        "user": users.get(a.user_id),
        "description": a.description, "status": a.status,
        "transaction_id": a.transaction_id,
        "date": a.created_at.isoformat() if a.created_at else None,
    } for a in rows],
        "counts": counts,
        "statuses": [{"key": k, "label": lbl}
                     for k, lbl in roles.FRAUD_STATUSES]}

@router.post("/api/gamification/fraud/{aid}")
def review_fraud(
    aid: int,
    payload: schemas.FraudReview,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.XP_ADMIN)),
):
    a = db.query(models.XpFraudAlert).get(aid)
    if not a:
        raise HTTPException(404, "Topilmadi")
    a.status = payload.status
    a.review_note = payload.note
    a.reviewed_by = user.id
    a.resolved_at = datetime.utcnow()
    db.commit()
    return {"ok": True}

@router.get("/api/gamification/analytics")
def gamification_analytics(
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.XP_ADMIN, *roles.FINANCE_ACCESS)),
):
    """CEO uchun: filial, guruh va ustoz kesimida XP, hamda XP bilan
    davomat va natija o'rtasidagi bog'liqlik."""
    gam = {g.student_id: g for g in db.query(models.StudentGamification).all()}
    students = db.query(models.Student).filter(
        models.Student.status.in_(["active", "trial"])).all()
    groups = {g.id: g for g in db.query(models.Group).all()}
    branches = {b.id: b.name for b in db.query(models.Branch).all()}
    teachers = {t.id: t.full_name for t in db.query(models.Teacher).all()}

    def agg(key_fn, label_fn):
        out: dict = {}
        for s in students:
            k = key_fn(s)
            if k is None:
                continue
            row = out.setdefault(k, {"students": 0, "xp": 0.0})
            row["students"] += 1
            row["xp"] += (gam[s.id].lifetime_xp or 0) if s.id in gam else 0
        return sorted([{
            "key": k, "label": label_fn(k),
            "students": v["students"],
            "total_xp": round(v["xp"], 1),
            "avg_xp": round(v["xp"] / v["students"], 1) if v["students"] else 0,
        } for k, v in out.items()], key=lambda r: -r["avg_xp"])

    by_branch = agg(lambda s: s.branch_id, lambda k: branches.get(k, "—"))
    by_group = agg(lambda s: s.group_id,
                   lambda k: groups[k].name if k in groups else "—")
    by_teacher = agg(
        lambda s: groups[s.group_id].teacher_id if s.group_id in groups else None,
        lambda k: teachers.get(k, "—"))

    # XP va davomat bog'liqligi
    pairs = []
    for s in students:
        g = gam.get(s.id)
        if not g:
            continue
        att = (db.query(models.Attendance)
               .filter(models.Attendance.student_id == s.id).all())
        if not att:
            continue
        rate = sum(1 for a in att if a.present) / len(att) * 100
        pairs.append((g.lifetime_xp or 0, rate))
    corr = None
    if len(pairs) >= 3:
        n = len(pairs)
        mx = sum(p[0] for p in pairs) / n
        my = sum(p[1] for p in pairs) / n
        num = sum((p[0] - mx) * (p[1] - my) for p in pairs)
        dx = sum((p[0] - mx) ** 2 for p in pairs) ** 0.5
        dy = sum((p[1] - my) ** 2 for p in pairs) ** 0.5
        corr = round(num / (dx * dy), 2) if dx and dy else None

    # Ustozlar qancha qo'lda XP berdi
    manual: dict = {}
    for t in (db.query(models.XpTransaction)
              .filter(models.XpTransaction.source_type == "manual").all()):
        if t.awarded_by_user_id:
            manual[t.awarded_by_user_id] = manual.get(t.awarded_by_user_id, 0) \
                + (t.amount or 0)
    unames = {u.id: u.full_name for u in db.query(models.User).all()}

    return {
        "by_branch": by_branch,
        "by_group": by_group[:20],
        "weakest_groups": by_group[-5:][::-1] if len(by_group) > 5 else [],
        "by_teacher": by_teacher,
        "attendance_correlation": corr,
        "correlation_hint": ("1 ga yaqin bo'lsa — XP ko'p bo'lgan o'quvchi "
                             "darsga ham ko'p keladi."),
        "manual_by_user": sorted([{
            "user": unames.get(k, "—"), "xp": round(v, 1)
        } for k, v in manual.items()], key=lambda r: -r["xp"])[:10],
    }

def _refresh_skill_score(db: Session, teacher_id: int) -> float | None:
    """Ustozning mahorat balli — oxirgi ASOSIY dars baholashining foizi.

    Nega oxirgisi: mahorat o'zgaradi, o'rtacha esa eski, allaqachon
    tuzatilgan kamchilikni yillar davomida sudrab yuradi."""
    last = (db.query(models.LessonObservation)
            .filter(models.LessonObservation.teacher_id == teacher_id,
                    models.LessonObservation.rubric_key == roles.RUBRIC_MAIN)
            .order_by(models.LessonObservation.date.desc(),
                      models.LessonObservation.id.desc()).first())
    if not last:
        return None
    t = db.query(models.Teacher).get(teacher_id)
    if t:
        t.skill_score = last.percent
    return last.percent

@router.post("/api/observations")
def create_observation(
    payload: schemas.ObservationCreate,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.OBSERVATION_ACCESS)),
):
    """Baholashni saqlaydi. Jami va foiz SERVERDA hisoblanadi — qo'lda
    yozib bo'lmaydi."""
    if payload.rubric_key not in roles.RUBRIC_LABELS:
        raise HTTPException(400, "Bunday baholash jadvali yo'q")
    if payload.target_type == "teacher" and not payload.teacher_id:
        raise HTTPException(400, "Ustozni tanlang")
    if payload.target_type == "candidate" and not payload.candidate_id:
        raise HTTPException(400, "Nomzodni tanlang")

    items = {c.id: c for c in _criteria(db, payload.rubric_key)}
    max_total = round(sum(c.points or 0 for c in items.values()), 1)

    total = 0.0
    clean = []
    for s in payload.scores:
        c = items.get(s.criterion_id)
        if not c:
            continue
        # Fakt mezon balidan oshmaydi va manfiy bo'lmaydi
        fact = max(0.0, min(float(s.fact or 0), float(c.points or 0)))
        total += fact
        clean.append((c.id, fact, s.note))

    percent = round(total / max_total * 100, 1) if max_total else 0.0
    band, _lbl, _tone = roles.rubric_band(percent)

    t = db.query(models.Teacher).get(payload.teacher_id) \
        if payload.teacher_id else None

    # Bosqich: berilmagan bo'lsa o'zi aniqlanadi. Nomzodning birinchi
    # baholashi "o'z holicha", ikkinchisi "tushuntirilgandan keyin".
    prev = (db.query(models.LessonObservation)
            .filter(models.LessonObservation.candidate_id
                    == payload.candidate_id)
            .count() if payload.candidate_id else 0)
    stage = payload.stage
    if not stage:
        if payload.candidate_id:
            stage = ("before" if prev == 0
                     else "coached" if prev == 1 else "extra")
        else:
            stage = "extra"

    obs = models.LessonObservation(
        rubric_key=payload.rubric_key,
        target_type=payload.target_type,
        stage=stage, attempt=prev + 1,
        teacher_id=payload.teacher_id,
        candidate_id=payload.candidate_id,
        group_id=payload.group_id,
        branch_id=t.branch_id if t else None,
        date=payload.date or date.today(),
        total=round(total, 1), max_total=max_total, percent=percent,
        band=band, strengths=payload.strengths,
        weaknesses=payload.weaknesses, note=payload.note,
        observer=user.full_name, observer_id=user.id)
    db.add(obs)
    db.flush()
    for cid, fact, note in clean:
        db.add(models.ObservationScore(observation_id=obs.id,
                                       criterion_id=cid, fact=fact,
                                       note=note))
    db.commit()

    # Natija ishga tushadi: ustozning mahorat balli, nomzodning
    # sinov darsi bali.
    if payload.teacher_id:
        _refresh_skill_score(db, payload.teacher_id)
        db.commit()
    if payload.candidate_id:
        cand = db.query(models.Candidate).get(payload.candidate_id)
        if cand:
            cand.trial_score = percent
            db.commit()

    return {
        "ok": True, "id": obs.id,
        "total": obs.total, "max_total": max_total, "percent": percent,
        "band": band, "band_label": roles.rubric_band(percent)[1],
        "passed": percent >= roles.TEACHER_MIN_SKILL,
        "stage": obs.stage,
        "stage_label": roles.STAGE_LABELS.get(obs.stage or "", "Baholash"),
        "attempt": obs.attempt,
    }

@router.get("/api/observations")
def list_observations(
    teacher_id: int | None = None,
    candidate_id: int | None = None,
    rubric_key: str | None = None,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """Baholashlar ro'yxati. Ustoz o'zinikini ko'ra oladi."""
    mine = _teacher_of_user(db, user)
    if user.role not in roles.OBSERVATION_ACCESS:
        if not mine or (teacher_id and teacher_id != mine.id):
            raise HTTPException(403, "Bu ma'lumot sizga ko'rinmaydi")
        teacher_id = mine.id

    q = db.query(models.LessonObservation)
    if teacher_id:
        q = q.filter(models.LessonObservation.teacher_id == teacher_id)
    if candidate_id:
        q = q.filter(models.LessonObservation.candidate_id == candidate_id)
    if rubric_key:
        q = q.filter(models.LessonObservation.rubric_key == rubric_key)
    rows = q.order_by(models.LessonObservation.date.desc(),
                      models.LessonObservation.id.desc()).limit(100).all()
    return {
        "rows": [_observation_out(db, o) for o in rows],
        "pass_score": roles.TEACHER_MIN_SKILL,
    }

@router.get("/api/observations/{oid}")
def get_observation(
    oid: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    o = db.query(models.LessonObservation).get(oid)
    if not o:
        raise HTTPException(404, "Topilmadi")
    mine = _teacher_of_user(db, user)
    if user.role not in roles.OBSERVATION_ACCESS and (
            not mine or mine.id != o.teacher_id):
        raise HTTPException(403, "Bu ma'lumot sizga ko'rinmaydi")
    return _observation_out(db, o, full=True)

@router.delete("/api/observations/{oid}")
def delete_observation(
    oid: int,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.GRADE_ADMIN)),
):
    o = db.query(models.LessonObservation).get(oid)
    if not o:
        raise HTTPException(404, "Topilmadi")
    tid = o.teacher_id
    db.delete(o)
    db.commit()
    if tid:
        _refresh_skill_score(db, tid)
        db.commit()
    return {"ok": True}

def _xp_for_certificate(db: Session, student_id: int, *, kind: str,
                        code: str, cert_no: str | None,
                        by_user: models.User, mode: str = roles.CERT_MODE_DIFF,
                        reason: str | None = None) -> dict:
    """Sertifikat XP'si. Bir sertifikat raqamiga qayta XP berilmaydi.
    Yangi va yuqoriroq natija olinsa — standart holatda faqat FARQI
    beriladi."""
    if cert_no:
        used = (db.query(models.XpTransaction)
                .filter(models.XpTransaction.idempotency_key
                        == f"CERT:{cert_no}").first())
        if used:
            _fraud_alert(db, "cert_reuse", student_id=student_id,
                         user_id=by_user.id, transaction_id=used.id,
                         description=f"Sertifikat raqami qayta ishlatildi: {cert_no}")
            db.commit()
            return {"ok": False, "skipped": True,
                    "reason": "Bu sertifikat raqamiga XP allaqachon berilgan"}

    ladder = roles.CERT_RULES.get(kind, [])
    rule = _xp_rule(db, code)
    if not rule:
        raise HTTPException(400, "Bunday sertifikat qoidasi yo'q")
    value = rule.default_xp or 0

    if mode == roles.CERT_MODE_DIFF and ladder:
        # Shu turdagi eng yuqori oldingi natija
        prev_best = 0
        for old in (db.query(models.XpTransaction)
                    .filter(models.XpTransaction.student_id == student_id,
                            models.XpTransaction.event_code.in_(ladder),
                            models.XpTransaction.is_reversal == 0).all()):
            prev_best = max(prev_best, old.amount or 0)
        if prev_best:
            value = max(0, value - prev_best)
            if value == 0:
                return {"ok": False, "skipped": True,
                        "reason": ("Oldingi sertifikat XP'si bundan yuqori "
                                   "yoki teng — qo'shimcha XP berilmaydi")}

    return award_xp(db, student_id=student_id, event_code=code,
                    amount=value, by_user=by_user,
                    source_type="certificate", reason=reason,
                    idempotency_key=(f"CERT:{cert_no}" if cert_no else None),
                    force=True)

