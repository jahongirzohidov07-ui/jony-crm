"""Auto-extracted from main.py during refactor (split-main). Domain: marketing."""
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

def _fetch_telegram_followers(handle: str) -> int | None:
    """Ochiq Telegram kanalining obunachilar sonini t.me sahifasidan
    o'qiydi. Token kerak emas - sahifa hammaga ochiq."""
    import re as _re
    import urllib.request
    try:
        req = urllib.request.Request(
            f"https://t.me/{handle}",
            headers={"User-Agent": "Mozilla/5.0 (compatible; JonyCRM/1.0)"},
        )
        with urllib.request.urlopen(req, timeout=10) as r:
            html = r.read().decode("utf-8", "ignore")
    except Exception:
        return None
    m = _re.search(r'tgme_page_extra">([\d\s \xa0,]+)\s*(?:subscribers|members|obuna)',
                   html, _re.I)
    if not m:
        m = _re.search(r'([\d\s \xa0,]{2,})\s*subscribers', html, _re.I)
    if not m:
        return None
    digits = _re.sub(r"\D", "", m.group(1))
    return int(digits) if digits else None

def _fetch_youtube_subscribers(handle: str) -> int | None:
    """YouTube kanalining obunachilar sonini ochiq sahifadan o'qiydi.
    Kanal @handle bilan ochiq bo'lsa token kerak emas."""
    import re as _re
    import urllib.request
    try:
        req = urllib.request.Request(
            f"https://www.youtube.com/@{handle}",
            headers={"User-Agent": "Mozilla/5.0 (compatible; JonyCRM/1.0)",
                     "Accept-Language": "en-US,en;q=0.9"},
        )
        with urllib.request.urlopen(req, timeout=12) as r:
            html = r.read().decode("utf-8", "ignore")
    except Exception:
        return None
    # "subscriberCountText":{"simpleText":"1.2K subscribers"} ko'rinishida
    m = _re.search(r'"subscriberCountText"\s*:\s*\{[^}]*?"(?:simpleText|content)"'
                   r'\s*:\s*"([^"]+)"', html)
    if not m:
        m = _re.search(r'([\d.,]+\s*[KMB]?)\s*subscribers', html, _re.I)
    if not m:
        return None
    txt = m.group(1).strip()
    num = _re.match(r"([\d.,]+)\s*([KMB])?", txt, _re.I)
    if not num:
        return None
    try:
        val = float(num.group(1).replace(",", ""))
    except ValueError:
        return None
    mult = {"K": 1_000, "M": 1_000_000, "B": 1_000_000_000}
    if num.group(2):
        val *= mult.get(num.group(2).upper(), 1)
    return int(val)

def _fetch_instagram_followers() -> int | None:
    """Instagram Graph API. Ishlashi uchun INSTAGRAM_TOKEN va
    INSTAGRAM_USER_ID muhit o'zgaruvchilari kerak (Business/Creator
    akkaunt + Facebook sahifa). Ular bo'lmasa None qaytaradi va
    oxirgi qo'lda kiritilgan qiymat saqlanib qoladi."""
    import json as _json
    import urllib.request
    token = os.getenv("INSTAGRAM_TOKEN")
    uid = os.getenv("INSTAGRAM_USER_ID")
    if not token or not uid:
        return None
    try:
        url = (f"https://graph.facebook.com/v19.0/{uid}"
               f"?fields=followers_count&access_token={token}")
        with urllib.request.urlopen(url, timeout=10) as r:
            data = _json.loads(r.read().decode())
        return int(data.get("followers_count"))
    except Exception:
        return None

def _latest_social(db: Session, platform: str):
    return (db.query(models.SocialStat)
            .filter(models.SocialStat.platform == platform)
            .order_by(models.SocialStat.date.desc(),
                      models.SocialStat.id.desc()).first())

def _save_social(db: Session, platform: str, followers: int, source: str):
    """Kunига bitta yozuv - shu kun uchun bo'lsa yangilanadi."""
    today = date.today()
    row = (db.query(models.SocialStat)
           .filter(models.SocialStat.platform == platform,
                   models.SocialStat.date == today).first())
    if row:
        row.followers = followers
        row.source = source
    else:
        db.add(models.SocialStat(platform=platform, followers=followers,
                                 source=source, date=today))
    db.commit()

@router.get("/api/social")
def social_stats(
    days: int = 90,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    since = date.today() - timedelta(days=max(7, min(days, 730)))

    # HAQIQIY AVTOMATIKA: bugungi o'lchov yo'q bo'lsa - o'zi olib keladi.
    # Ya'ni kuniga bir marta, birinchi ochgan odam uchun yangilanadi va
    # hech kim "Yangilash" tugmasini bosib yurishi shart emas.
    # Xatolik bo'lsa jim o'tadi - dashboard baribir ochilishi kerak.
    try:
        if not _latest_social(db, "telegram") or \
           _latest_social(db, "telegram").date != date.today():
            tg = _fetch_telegram_followers(roles.SOCIAL_HANDLES["telegram"])
            if tg:
                _save_social(db, "telegram", tg, "auto")
        yt_last = _latest_social(db, "youtube")
        if not yt_last or yt_last.date != date.today():
            yt = _fetch_youtube_subscribers(roles.SOCIAL_HANDLES["youtube"])
            if yt:
                _save_social(db, "youtube", yt, "auto")
        ig_last = _latest_social(db, "instagram")
        if os.getenv("INSTAGRAM_TOKEN") and (
            not ig_last or ig_last.date != date.today()
        ):
            ig = _fetch_instagram_followers()
            if ig:
                _save_social(db, "instagram", ig, "auto")
    except Exception:
        pass

    out = {}
    for key, label in roles.SOCIAL_PLATFORMS:
        last = _latest_social(db, key)
        hist = (db.query(models.SocialStat)
                .filter(models.SocialStat.platform == key,
                        models.SocialStat.date >= since)
                .order_by(models.SocialStat.date).all())
        prev = hist[0].followers if len(hist) > 1 else None
        out[key] = {
            "platform": key,
            "label": label,
            "handle": roles.SOCIAL_HANDLES.get(key),
            "followers": last.followers if last else None,
            "source": last.source if last else None,
            "date": last.date.isoformat() if last and last.date else None,
            "growth": (last.followers - prev) if last and prev is not None else None,
            "history": [{"date": h.date.isoformat(), "followers": h.followers}
                        for h in hist],
        }
    return out

@router.post("/api/social/refresh")
def social_refresh(
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.MARKETING_ACCESS)),
):
    """Telegram - avtomat o'qiydi. Instagram - token bo'lsa o'qiydi."""
    result = {}
    tg = _fetch_telegram_followers(roles.SOCIAL_HANDLES["telegram"])
    if tg:
        _save_social(db, "telegram", tg, "auto")
    result["telegram"] = tg

    yt = _fetch_youtube_subscribers(roles.SOCIAL_HANDLES["youtube"])
    if yt:
        _save_social(db, "youtube", yt, "auto")
    result["youtube"] = yt

    ig = _fetch_instagram_followers()
    if ig:
        _save_social(db, "instagram", ig, "auto")
    result["instagram"] = ig
    result["instagram_note"] = (
        None if ig else
        "Instagram uchun rasmiy token kerak (INSTAGRAM_TOKEN + "
        "INSTAGRAM_USER_ID). Hozircha qo'lda kiriting."
    )
    return result

@router.post("/api/social/manual")
def social_manual(
    payload: schemas.SocialManual,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.MARKETING_ACCESS)),
):
    if payload.platform not in dict(roles.SOCIAL_PLATFORMS):
        raise HTTPException(400, "Noma'lum platforma")
    _save_social(db, payload.platform, payload.followers, "manual")
    return {"ok": True}

@router.get("/api/ad-stats")
def list_ad_stats(
    months: int = 12,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.MARKETING_ACCESS)),
):
    today = date.today()
    periods = []
    for back in range(months - 1, -1, -1):
        y, m = _shift_month(today.year, today.month, -back)
        periods.append(_period_key(y, m))
    q = scope_to_branch(db.query(models.AdStat), models.AdStat, user).filter(
        models.AdStat.period.in_(periods))
    return [{
        "id": a.id, "channel": a.channel,
        "label": roles.MARKETING_CHANNEL_LABELS.get(a.channel, a.channel),
        "period": a.period, "impressions": a.impressions, "clicks": a.clicks,
        "ctr": round(a.clicks / a.impressions * 100, 2) if a.impressions else 0.0,
        "branch_id": a.branch_id, "note": a.note,
    } for a in q.order_by(models.AdStat.period.desc()).all()]

@router.post("/api/ad-stats")
def upsert_ad_stat(
    payload: schemas.AdStatCreate,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.MARKETING_ACCESS)),
):
    """Bir kanal + bir oy uchun bitta yozuv. Qayta yuborilsa
    yangilanadi - takror qator paydo bo'lmaydi."""
    if payload.channel not in roles.MARKETING_CHANNELS:
        raise HTTPException(400, "Noma'lum kanal")
    row = (db.query(models.AdStat)
           .filter(models.AdStat.channel == payload.channel,
                   models.AdStat.period == payload.period).first())
    if row:
        row.impressions = payload.impressions
        row.clicks = payload.clicks
        row.note = payload.note
    else:
        row = models.AdStat(**payload.model_dump(), created_by=user.full_name)
        db.add(row)
    db.commit(); db.refresh(row)
    return {"id": row.id}

@router.delete("/api/ad-stats/{stat_id}")
def delete_ad_stat(
    stat_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.MARKETING_ACCESS)),
):
    a = db.query(models.AdStat).get(stat_id)
    if not a:
        raise HTTPException(404, "Topilmadi")
    db.delete(a); db.commit()
    return {"ok": True}

@router.get("/api/marketing/rfm")
def marketing_rfm(
    branch_id: int | None = None,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.MARKETING_ANALYTICS)),
):
    today = date.today()
    students = scope_to_branch(db.query(models.Student), models.Student,
                               user, branch_id).filter(
        models.Student.status != "archived").all()
    if not students:
        return {"rows": [], "segments": [], "total": 0}

    ids = [s.id for s in students]
    last = {}
    agg = {}
    for sid, mx, cnt, total in (
            db.query(models.Payment.student_id,
                     func.max(models.Payment.created_at),
                     func.count(models.Payment.id),
                     func.sum(models.Payment.amount))
            .filter(models.Payment.student_id.in_(ids),
                    models.Payment.kind == "payment")
            .group_by(models.Payment.student_id).all()):
        last[sid] = mx
        agg[sid] = (cnt or 0, total or 0.0)

    rows = []
    for s in students:
        cnt, total = agg.get(s.id, (0, 0.0))
        lastp = last.get(s.id)
        days = ((today - lastp.date()).days if lastp
                else (today - (s.enrolled_date or today)).days)
        r, f, m, seg = roles.rfm_score(days, cnt, total)
        info = roles.RFM_SEGMENT_INFO[seg]
        rows.append({
            "student_id": s.id,
            "full_name": s.full_name,
            "phone": s.phone or s.parent_phone,
            "group": s.group.name if s.group else None,
            "status": s.status,
            "r": r, "f": f, "m": m,
            "days_since_payment": days,
            "payments": cnt,
            "total_paid": round(total, 2),
            "balance": round(student_balance(db, s.id), 2),
            "segment": seg,
            "segment_label": info["label"],
            "tone": info["tone"],
            "action": info["action"],
        })

    by_seg = {}
    for r in rows:
        b = by_seg.setdefault(r["segment"], {"count": 0, "revenue": 0.0})
        b["count"] += 1
        b["revenue"] += r["total_paid"]

    segments = []
    for key, label, hint, tone, action in roles.RFM_SEGMENTS:
        b = by_seg.get(key, {"count": 0, "revenue": 0.0})
        segments.append({
            "key": key, "label": label, "hint": hint, "tone": tone,
            "action": action,
            "count": b["count"],
            "revenue": round(b["revenue"], 2),
            "percent": round(b["count"] / len(rows) * 100, 1) if rows else 0.0,
        })

    rows.sort(key=lambda r: (-r["m"], -r["f"], -r["r"]))
    return {
        "rows": rows,
        "segments": segments,
        "total": len(rows),
        "hint": ("R — oxirgi to'lovdan beri o'tgan vaqt, "
                 "F — to'lovlar soni, M — jami summa. "
                 "Har bir segment uchun aniq harakat taklif qilingan."),
    }

