"""INSTAGRAM ULASH (2026-09-26).

Jahongir: "Keyin instagramni ulaylik unda avtomat ko'rinishi kerak,
telegramdan kora bizga instagram muhim. Shuni ulab ber o'zing to'liq."

QANDAY ISHLAYDI:
  1. Asoschi (yoki SMM menejer) Meta'dan olingan tokenni JonyOS'dagi
     "Instagram" oynasiga O'ZI joylaydi. Token bazada saqlanadi, API
     javobida hech qachon to'liq qaytmaydi (faqat oxirgi 4 belgisi).
  2. Akkaunt raqami avtomat topiladi:
       - Facebook tokeni (EAA...)  -> /me/accounts -> instagram_business_account
       - Instagram Login tokeni (IG...) -> graph.instagram.com/me
  3. Har kuni (cron) va "Hozir yangilash" tugmasida oxirgi postlar
     o'qiladi: like, izoh, ko'rish, qamrov, saqlash, ulashish, obuna
     bo'lganlar, profilga o'tishlar.
  4. Har post kontent-plandagi postga bog'lanadi:
       a) post_url ichidagi shortcode bo'yicha;
       b) bo'lmasa — shu kunga rejalangan, havolasiz BITTA Instagram
          posti bo'lsa, o'shanga (havolasi ham avtomat yoziladi);
       c) bo'lmasa — rejaga "Instagram'dan avtomat" deb yangi qator
          qo'shiladi (holati "joylandi"). Shunda HAR BIR video tahlilda
          ko'rinadi, hech biri tushib qolmaydi.
     Bog'langan postning raqamlari ContentMetric'ga yoziladi.

HECH NARSA O'CHIRILMAYDI. Uzish tokenni bo'shatadi, sinxron qilingan
postlar va raqamlar joyida qoladi.
"""
import os
import re
import json
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, datetime, timedelta

from fastapi import APIRouter, Body, Depends, HTTPException
from sqlalchemy.orm import Session

import audit
import models
import roles
from auth import require_role
from database import get_db, SessionLocal

router = APIRouter()

FB = "https://graph.facebook.com/v21.0"
IGG = "https://graph.instagram.com/v21.0"

K_TOKEN = "instagram_token"
K_USER = "instagram_user_id"
K_NAME = "instagram_username"
K_API = "instagram_api"          # "fb" | "ig"
K_LAST = "instagram_last_sync"
K_LAST_NOTE = "instagram_last_note"

TOKEN_ROLES = list(dict.fromkeys(roles.FULL_ACCESS + [roles.SMM_MANAGER]))

# Testlar tarmoqqa chiqmasligi uchun almashtiriladigan HTTP funksiya
def _http_get(url: str, timeout: int = 20) -> dict:
    req = urllib.request.Request(
        url, headers={"User-Agent": "JonyCRM/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8", "ignore"))
    except urllib.error.HTTPError as e:
        try:
            body = json.loads(e.read().decode("utf-8", "ignore"))
            msg = (body.get("error") or {}).get("message") or str(e)
        except Exception:
            msg = str(e)
        raise RuntimeError(msg)


HTTP = {"get": _http_get}


def _get(url: str, **params) -> dict:
    q = urllib.parse.urlencode(params)
    return HTTP["get"](url + ("&" if "?" in url else "?") + q)


# ------------------------------------------------------------ sozlamalar
def _s(db: Session, key: str) -> str:
    row = db.query(models.IntegrationSetting).get(key)
    return (row.value or "") if row else ""


def _set(db: Session, key: str, value: str | None, who: str | None):
    row = db.query(models.IntegrationSetting).get(key)
    if row is None:
        row = models.IntegrationSetting(key=key)
        db.add(row)
    row.value = value
    row.updated_by = who
    row.updated_at = datetime.utcnow()


def creds(db: Session | None = None) -> tuple:
    """(token, user_id, api) — bazadan, bo'lmasa muhit o'zgaruvchisidan.
    content_fetch va marketing ham shuni ishlatadi."""
    own = db is None
    try:
        if own:
            db = SessionLocal()
        tok, uid, api = _s(db, K_TOKEN), _s(db, K_USER), _s(db, K_API)
    except Exception:
        tok, uid, api = "", "", ""
    finally:
        if own and db is not None:
            try:
                db.close()
            except Exception:
                pass
    if not tok:
        tok = (os.getenv("INSTAGRAM_TOKEN") or "").strip()
        uid = uid or (os.getenv("INSTAGRAM_USER_ID") or "").strip()
    if not api:
        api = "ig" if tok.startswith("IG") else "fb"
    return tok, uid, api


def _base(api: str) -> str:
    return IGG if api == "ig" else FB


def _mask(tok: str) -> str:
    return ("•••• " + tok[-4:]) if tok else ""


def discover(token: str) -> dict:
    """Token qaysi Instagram akkauntga tegishli — topib beradi."""
    token = (token or "").strip()
    if token.startswith("IG"):
        me = _get(f"{IGG}/me", fields="user_id,username,followers_count",
                  access_token=token)
        uid = str(me.get("user_id") or me.get("id") or "")
        if not uid:
            raise RuntimeError("Instagram akkaunti topilmadi")
        return {"api": "ig", "user_id": uid,
                "username": me.get("username") or "",
                "followers": me.get("followers_count")}
    acc = _get(f"{FB}/me/accounts",
               fields="name,instagram_business_account{id,username,"
                      "followers_count}",
               access_token=token)
    for page in acc.get("data") or []:
        ig = page.get("instagram_business_account") or {}
        if ig.get("id"):
            return {"api": "fb", "user_id": str(ig["id"]),
                    "username": ig.get("username") or page.get("name") or "",
                    "followers": ig.get("followers_count")}
    raise RuntimeError(
        "Bu tokenga bog'langan Facebook sahifada Instagram Business "
        "akkaunt topilmadi. Instagram akkaunt 'Professional' bo'lishi va "
        "Facebook sahifaga ulangan bo'lishi kerak.")


# ------------------------------------------------------------ sinxron
_SC = re.compile(r"instagram\.com/(?:[A-Za-z0-9_.]+/)?(?:p|reel|reels|tv)/"
                 r"([A-Za-z0-9_-]+)")


def shortcode(url: str | None) -> str:
    m = _SC.search(url or "")
    return m.group(1) if m else ""


_METRICS_FULL = "reach,saved,shares,views,follows,profile_visits"
_METRICS_SAFE = "reach,saved,shares"


def _insights(base: str, mid: str, token: str) -> dict:
    out = {}
    for metric in (_METRICS_FULL, _METRICS_SAFE):
        try:
            r = _get(f"{base}/{mid}/insights", metric=metric,
                     access_token=token)
        except Exception:
            continue
        for it in r.get("data") or []:
            vals = it.get("values") or [{}]
            v = vals[0].get("value") if vals else None
            if v is None:
                v = (it.get("total_value") or {}).get("value")
            out[it.get("name")] = int(v or 0)
        break
    return out


def _title_of(caption: str | None, posted: date | None) -> str:
    first = (caption or "").strip().splitlines()[0] if caption else ""
    first = re.sub(r"\s+", " ", first)[:90]
    return first or f"Instagram post {posted.isoformat() if posted else ''}".strip()


def _apply_metric(db: Session, content_id: int, m: models.IgMedia):
    met = (db.query(models.ContentMetric)
           .filter(models.ContentMetric.content_id == content_id).first())
    if not met:
        met = models.ContentMetric(content_id=content_id)
        db.add(met)
    for k in ("views", "reach", "likes", "comments", "shares", "saves",
              "follows", "profile_visits"):
        v = int(getattr(m, k) or 0)
        if v:                           # 0 kelsa qo'lda yozilgan qoladi
            setattr(met, k, v)
    met.source = "auto"
    met.updated_by = "Instagram"
    met.fetched_at = datetime.utcnow()
    met.fetch_note = "Instagram rasmiy API (avtomat sinxron)"


def _link(db: Session, m: models.IgMedia, auto_create: bool) -> str:
    """Postni kontent-plandagi qatorga bog'lash. Qaytaradi: qanday
    bog'langani (sc | day | new | none)."""
    if m.content_id:
        return "kept"
    sc = m.shortcode
    if sc:
        hit = (db.query(models.Content)
               .filter(models.Content.post_url.ilike(f"%{sc}%")).first())
        if hit:
            m.content_id = hit.id
            m.link_note = "havola bo'yicha"
            return "sc"
    posted = m.posted_at.date() if m.posted_at else None
    if posted:
        cands = (db.query(models.Content)
                 .filter(models.Content.platform == "instagram",
                         models.Content.planned_date == posted,
                         models.Content.status != "cancelled",
                         (models.Content.post_url.is_(None))
                         | (models.Content.post_url == ""))
                 .all())
        taken = {x for (x,) in db.query(models.IgMedia.content_id)
                 .filter(models.IgMedia.content_id.isnot(None)).all()}
        cands = [c for c in cands if c.id not in taken]
        if len(cands) == 1:
            c = cands[0]
            m.content_id = c.id
            m.link_note = "shu kungi reja bo'yicha"
            c.post_url = m.permalink
            if c.status not in roles.CONTENT_LIVE:
                c.status = "published"
            c.published_at = c.published_at or m.posted_at
            return "day"
    if not auto_create:
        return "none"
    c = models.Content(
        title=_title_of(m.caption, posted), platform="instagram",
        planned_date=posted, status="published", post_url=m.permalink,
        published_at=m.posted_at, caption=m.caption,
        fmt="reels" if (m.media_type or "").upper() == "VIDEO" else None,
        created_by="Instagram sinxron",
        note="Instagram'dan avtomat qo'shildi (rejada yo'q edi)")
    db.add(c)
    db.flush()
    try:
        c.content_id = f"CONTENT-JA-{(posted or date.today()).year}-{c.id:04d}"
    except Exception:
        pass
    m.content_id = c.id
    m.link_note = "avtomat qo'shildi"
    return "new"


def sync(db: Session, days: int = 60, auto_create: bool = True,
         who: str = "avtomat") -> dict:
    tok, uid, api = creds(db)
    if not tok:
        return {"ok": False, "note": "Instagram ulanmagan (token yo'q)"}
    base = _base(api)
    try:
        if not uid:
            info = discover(tok)
            uid, api = info["user_id"], info["api"]
            base = _base(api)
            _set(db, K_USER, uid, who)
            _set(db, K_API, api, who)
            _set(db, K_NAME, info.get("username"), who)
        path = f"{base}/{uid}/media"
        fields = ("id,caption,media_type,media_product_type,permalink,"
                  "timestamp,like_count,comments_count")
        page = _get(path, fields=fields, limit=50, access_token=tok)
    except Exception as e:
        note = f"Instagram javob bermadi: {e}"[:250]
        _set(db, K_LAST_NOTE, note, who)
        db.commit()
        return {"ok": False, "note": note}

    since = datetime.utcnow() - timedelta(days=days)
    seen = made = linked = updated = 0
    stop = False
    pages = 0
    while page and not stop and pages < 6:
        pages += 1
        for it in page.get("data") or []:
            ts = it.get("timestamp")
            try:
                posted = datetime.strptime(ts[:19], "%Y-%m-%dT%H:%M:%S") \
                    if ts else None
            except ValueError:
                posted = None
            if posted and posted < since:
                stop = True
                break
            seen += 1
            m = (db.query(models.IgMedia)
                 .filter(models.IgMedia.ig_id == str(it["id"])).first())
            if not m:
                m = models.IgMedia(ig_id=str(it["id"]))
                db.add(m)
            m.permalink = it.get("permalink")
            m.shortcode = shortcode(m.permalink)
            m.caption = it.get("caption")
            m.media_type = it.get("media_type")
            m.posted_at = posted
            m.likes = int(it.get("like_count") or 0)
            m.comments = int(it.get("comments_count") or 0)
            ins = _insights(base, str(it["id"]), tok)
            m.reach = ins.get("reach", m.reach or 0)
            m.saves = ins.get("saved", m.saves or 0)
            m.shares = ins.get("shares", m.shares or 0)
            m.views = ins.get("views", ins.get("plays", m.views or 0))
            m.follows = ins.get("follows", m.follows or 0)
            m.profile_visits = ins.get("profile_visits",
                                       m.profile_visits or 0)
            m.fetched_at = datetime.utcnow()
            db.flush()
            how = _link(db, m, auto_create)
            if how == "new":
                made += 1
            elif how in ("sc", "day"):
                linked += 1
            if m.content_id:
                _apply_metric(db, m.content_id, m)
                updated += 1
        nxt = (page.get("paging") or {}).get("next")
        if stop or not nxt:
            break
        try:
            page = HTTP["get"](nxt)
        except Exception:
            break

    note = (f"{seen} ta post o'qildi, {updated} tasining raqamlari "
            f"yangilandi, {linked} tasi rejaga bog'landi, {made} tasi "
            f"rejaga avtomat qo'shildi")
    _set(db, K_LAST, datetime.utcnow().isoformat(timespec="seconds"), who)
    _set(db, K_LAST_NOTE, note, who)
    db.commit()
    # Obunachilar soni ham (dashboard kartasi)
    try:
        fl = followers(db)
        if fl is not None:
            from marketing import _save_social
            _save_social(db, "instagram", fl, "api")
    except Exception:
        db.rollback()
    return {"ok": True, "seen": seen, "updated": updated,
            "linked": linked, "created": made, "note": note}


def followers(db: Session | None = None) -> int | None:
    tok, uid, api = creds(db)
    if not (tok and uid):
        return None
    try:
        r = _get(f"{_base(api)}/{uid}", fields="followers_count",
                 access_token=tok)
        return int(r.get("followers_count"))
    except Exception:
        return None


def cron_sync(db: Session) -> dict:
    """system.py kunlik cron'i chaqiradi. Token bo'lmasa jim o'tadi."""
    tok, _, _ = creds(db)
    if not tok:
        return {"ok": False, "note": "token yo'q"}
    return sync(db, days=30, who="cron")


# ------------------------------------------------------------ API
@router.get("/api/smm/instagram")
def ig_status(db: Session = Depends(get_db),
              user=Depends(require_role(*roles.SMM_ACCESS))):
    tok, uid, api = creds(db)
    rows = (db.query(models.IgMedia)
            .order_by(models.IgMedia.posted_at.desc()).limit(60).all())
    titles = {}
    ids = [r.content_id for r in rows if r.content_id]
    att = {}
    if ids:
        titles = {c.id: c.title for c in db.query(models.Content)
                  .filter(models.Content.id.in_(ids)).all()}
        try:
            from content import attribution_by_content
            att = attribution_by_content(db, ids)
        except Exception:
            att = {}
    return {
        "connected": bool(tok),
        "from_env": bool(tok) and not _s(db, K_TOKEN),
        "token": _mask(tok),
        "account_id": uid or None,
        "username": _s(db, K_NAME) or None,
        "api": api if tok else None,
        "last_sync": _s(db, K_LAST) or None,
        "last_note": _s(db, K_LAST_NOTE) or None,
        "can_set_token": user.role in TOKEN_ROLES,
        "posts": [{
            "id": r.id, "permalink": r.permalink, "type": r.media_type,
            "caption": (r.caption or "")[:120],
            "posted_at": r.posted_at.isoformat() if r.posted_at else None,
            "views": r.views, "reach": r.reach, "likes": r.likes,
            "comments": r.comments, "saves": r.saves, "shares": r.shares,
            "follows": r.follows, "profile_visits": r.profile_visits,
            "content_id": r.content_id,
            "content_title": titles.get(r.content_id),
            "link_note": r.link_note,
            # Shu postdan kelgan murojaat / lid / sotuv / tushum
            **{k: (att.get(r.content_id) or {}).get(k, 0)
               for k in ("messages", "leads", "sales", "revenue")},
        } for r in rows],
    }


@router.post("/api/smm/instagram/token")
def ig_set_token(payload: dict = Body(...), db: Session = Depends(get_db),
                 user=Depends(require_role(*TOKEN_ROLES))):
    tok = (payload.get("token") or "").strip()
    if len(tok) < 20:
        raise HTTPException(400, "Token juda qisqa — to'liq nusxalang")
    try:
        info = discover(tok)
    except Exception as e:
        raise HTTPException(400, f"Token ishlamadi: {e}")
    _set(db, K_TOKEN, tok, user.full_name)
    _set(db, K_USER, info["user_id"], user.full_name)
    _set(db, K_API, info["api"], user.full_name)
    _set(db, K_NAME, info.get("username"), user.full_name)
    db.commit()
    audit.log(db, user, entity="integration", action="update",
              entity_label="Instagram",
              note=f"Instagram ulandi: @{info.get('username')} "
                   f"(token {_mask(tok)})")
    db.commit()
    res = sync(db, who=user.full_name)
    return {"ok": True, "username": info.get("username"),
            "account_id": info["user_id"], "sync": res}


@router.post("/api/smm/instagram/disconnect")
def ig_disconnect(db: Session = Depends(get_db),
                  user=Depends(require_role(*TOKEN_ROLES))):
    old = _s(db, K_TOKEN)
    _set(db, K_TOKEN, "", user.full_name)
    db.commit()
    audit.log(db, user, entity="integration", action="update",
              entity_label="Instagram",
              note=f"Instagram uzildi (token {_mask(old)} bo'shatildi; "
                   "sinxron qilingan postlar joyida)")
    db.commit()
    return {"ok": True}


@router.post("/api/smm/instagram/sync")
def ig_sync_now(db: Session = Depends(get_db),
                user=Depends(require_role(*roles.SMM_ACCESS))):
    return sync(db, who=user.full_name)


@router.post("/api/smm/instagram/link")
def ig_link(payload: dict = Body(...), db: Session = Depends(get_db),
            user=Depends(require_role(*roles.SMM_ACCESS))):
    """Avtomat noto'g'ri bog'lagan bo'lsa — qo'lda boshqa postga."""
    m = db.query(models.IgMedia).get(int(payload.get("media_id") or 0))
    c = db.query(models.Content).get(int(payload.get("content_id") or 0))
    if not m or not c:
        raise HTTPException(404, "Post yoki kontent topilmadi")
    m.content_id = c.id
    m.link_note = f"qo'lda bog'landi ({user.full_name})"
    if not c.post_url:
        c.post_url = m.permalink
    _apply_metric(db, c.id, m)
    db.commit()
    return {"ok": True}
