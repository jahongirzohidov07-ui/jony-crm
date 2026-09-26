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
        # Platforma turlicha yozilgan bo'lishi mumkin: "instagram",
        # "Instagram Reels" (Exceldan), ig_reels/ig_post/ig_story
        from sqlalchemy import func as _f, or_ as _or
        plat = _or(_f.lower(models.Content.platform).like("%insta%"),
                   models.Content.platform.in_(
                       ["ig_post", "ig_reels", "ig_story"]))
        cands = (db.query(models.Content)
                 .filter(plat,
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


K_CURSOR = "instagram_full_cursor"
K_FULL_DONE = "instagram_full_done"
BASE_FIELDS = ("id,caption,media_type,media_product_type,permalink,"
               "timestamp,like_count,comments_count")
_NESTED = ("insights.metric(reach,saved,shares,views,follows,"
           "profile_visits)", "insights.metric(reach,saved,shares)")


def _first_page(path: str, tok: str) -> tuple:
    """Insightslarni media bilan BIRGA so'raymiz (50 post = 1 so'rov).
    Meta biror metrikani rad etsa — xavfsizroq to'plam, u ham bo'lmasa
    oddiy maydonlar (unda insights har post uchun alohida)."""
    last = None
    for extra in _NESTED + ("",):
        f = BASE_FIELDS + ("," + extra if extra else "")
        try:
            return _get(path, fields=f, limit=50, access_token=tok), bool(extra)
        except Exception as e:
            last = e
    raise last


def _parse_ins(it: dict) -> dict | None:
    blk = it.get("insights")
    if not isinstance(blk, dict):
        return None
    out = {}
    for x in blk.get("data") or []:
        vals = x.get("values") or [{}]
        v = vals[0].get("value") if vals else None
        if v is None:
            v = (x.get("total_value") or {}).get("value")
        out[x.get("name")] = int(v or 0)
    return out


def sync(db: Session, days: int | None = 60, auto_create: bool = True,
         who: str = "avtomat", full: bool = False,
         create_days: int = 60, budget_s: float = 45.0) -> dict:
    """days — shuncha kunlik postlar yangilanadi. full=True — akkauntdagi
    HAMMA postlar (2026-09-26, Jahongir: "hamma JonyAcademy kanalidagi
    videolar statistikasi menda korinsa"). Vaqt chegarasi (budget_s)
    oshsa, qolgan joy "cursor" bilan saqlanadi va keyingi safar (cron
    yoki tugma) o'sha joydan davom etadi — Vercel vaqt limitiga
    tushmaslik uchun. Rejaga avtomat qator faqat oxirgi create_days
    kundagi postlar uchun qo'shiladi — eski yuzlab postlar kontent-
    planni to'ldirib yubormasin (ular Instagram jadvalida ko'rinadi)."""
    import time as _t
    t0 = _t.time()
    tok, uid, api = creds(db)
    if not tok:
        return {"ok": False, "note": "Instagram ulanmagan (token yo'q)"}
    base = _base(api)
    nested = True
    try:
        if not uid:
            info = discover(tok)
            uid, api = info["user_id"], info["api"]
            base = _base(api)
            _set(db, K_USER, uid, who)
            _set(db, K_API, api, who)
            _set(db, K_NAME, info.get("username"), who)
        cursor = _s(db, K_CURSOR) if full else ""
        if cursor:
            page = HTTP["get"](cursor)
            nested = "insights.metric" in cursor
        else:
            page, nested = _first_page(f"{base}/{uid}/media", tok)
    except Exception as e:
        note = f"Instagram javob bermadi: {e}"[:250]
        _set(db, K_LAST_NOTE, note, who)
        db.commit()
        return {"ok": False, "note": note}

    now = datetime.utcnow()
    since = None if full else now - timedelta(days=days or 60)
    create_since = now - timedelta(days=create_days)
    seen = made = linked = updated = 0
    stop = partial = False
    pages = 0
    while page and not stop and pages < 60:
        pages += 1
        for it in page.get("data") or []:
            ts = it.get("timestamp")
            try:
                posted = datetime.strptime(ts[:19], "%Y-%m-%dT%H:%M:%S") \
                    if ts else None
            except ValueError:
                posted = None
            if since and posted and posted < since:
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
            ins = _parse_ins(it)
            if ins is None:
                ins = _insights(base, str(it["id"]), tok)
            m.reach = ins.get("reach", m.reach or 0)
            m.saves = ins.get("saved", m.saves or 0)
            m.shares = ins.get("shares", m.shares or 0)
            m.views = ins.get("views", ins.get("plays", m.views or 0))
            m.follows = ins.get("follows", m.follows or 0)
            m.profile_visits = ins.get("profile_visits",
                                       m.profile_visits or 0)
            m.fetched_at = now
            db.flush()
            fresh = bool(posted and posted >= create_since)
            how = _link(db, m, auto_create and fresh)
            if how == "new":
                made += 1
            elif how in ("sc", "day"):
                linked += 1
            if m.content_id:
                _apply_metric(db, m.content_id, m)
                updated += 1
        db.commit()
        nxt = (page.get("paging") or {}).get("next")
        if stop or not nxt:
            if full:
                _set(db, K_CURSOR, "", who)
                _set(db, K_FULL_DONE, now.isoformat(timespec="seconds"), who)
            break
        if _t.time() - t0 > budget_s:
            partial = True
            if full:
                _set(db, K_CURSOR, nxt, who)
            break
        try:
            page = HTTP["get"](nxt)
        except Exception:
            break

    note = (f"{seen} ta post o'qildi, {updated} tasining raqamlari "
            f"yangilandi, {linked} tasi rejaga bog'landi, {made} tasi "
            f"rejaga avtomat qo'shildi")
    if partial and full:
        note += ". Postlar ko'p — qolganlari keyingi yangilanishda davom etadi"
    total = db.query(models.IgMedia).count()
    note += f". Jami bazada: {total} ta post"
    _set(db, K_LAST, now.isoformat(timespec="seconds"), who)
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
            "linked": linked, "created": made, "note": note,
            "partial": partial, "total": total}


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
    if not _s(db, K_FULL_DONE):
        return sync(db, full=True, who="cron")
    return sync(db, days=30, who="cron")


# ------------------------------------------------------------ API
@router.get("/api/smm/instagram")
def ig_status(db: Session = Depends(get_db),
              user=Depends(require_role(*roles.SMM_ACCESS))):
    tok, uid, api = creds(db)
    rows = (db.query(models.IgMedia)
            .order_by(models.IgMedia.posted_at.desc()).limit(1000).all())
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
        # "Facebook orqali ulash" uchun (secret hech qachon qaytmaydi)
        "app_id": app_creds(db)[0] or None,
        "has_secret": bool(app_creds(db)[1]),
        "config_id": config_id(db) or None,
        "redirect_uri": redirect_uri(),
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
    # Ulanganda — akkauntdagi HAMMA postlar (vaqt yetmasa davomi cron'da)
    _set(db, K_CURSOR, "", user.full_name)
    _set(db, K_FULL_DONE, "", user.full_name)
    db.commit()
    res = sync(db, who=user.full_name, full=True)
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
    # To'liq tarix hali tugamagan bo'lsa — o'sha joydan davom etadi
    return sync(db, who=user.full_name, full=not _s(db, K_FULL_DONE))


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


# =====================================================================
#  "FACEBOOK ORQALI ULASH" — TOKEN KO'CHIRMASDAN (2026-09-26)
#
#  Jahongir: "instagramni qilib ber qanday qilaman ozing qilib ber
#  hammasini". Token ko'chirib joylash murakkab va 60 kunda eskiradi.
#  Shuning uchun oddiy OAuth: JonyOS'da tugma -> Facebook "ruxsat
#  berasizmi?" -> qaytib keladi -> tayyor.
#
#  Qanday tuzilgan:
#    1. Meta ilovasining App ID va App Secret'i bazada (integration_
#       settings) yoki muhit o'zgaruvchisida (META_APP_ID/SECRET).
#       Secret javobda hech qachon qaytmaydi.
#    2. /oauth/start — imzolangan "state" (kim, qachongacha) bilan
#       Facebook dialog havolasini qaytaradi.
#    3. /oauth/callback — Facebook qaytargan kodni tokenga, uni uzoq
#       muddatli tokenga almashtiradi, keyin SAHIFA tokenini oladi:
#       uzoq muddatli foydalanuvchi tokenidan olingan sahifa tokenining
#       muddati TUGAMAYDI. Instagram Business akkaunt shu sahifadan.
#    4. Darrov sinxron qilinadi va SMM -> Instagram oynasiga qaytadi.
# =====================================================================
import base64 as _b64
import hashlib as _hl
import hmac as _hmac
import time as _time

from fastapi.responses import RedirectResponse

K_APP_ID = "meta_app_id"
K_APP_SECRET = "meta_app_secret"
# Facebook Login for Business: ruxsatlar "configuration" orqali beriladi
# (scope o'rniga config_id). JonyOS ilovasi uchun 2026-09-26 da Meta'da
# "JonyOS Instagram statistika" konfiguratsiyasi yaratildi.
K_CONFIG_ID = "meta_config_id"
KNOWN_CONFIGS = {"1614151326992230": "1127900133139057"}
OAUTH_SCOPES = ("instagram_basic,instagram_manage_insights,"
                "pages_show_list,pages_read_engagement,business_management")
CALLBACK_PATH = "/api/smm/instagram/oauth/callback"


def _public_base() -> str:
    b = (os.getenv("PUBLIC_URL") or "https://jonyos.uz").strip().rstrip("/")
    if not b.startswith("http"):
        b = "https://" + b
    return b


def redirect_uri() -> str:
    return _public_base() + CALLBACK_PATH


def app_creds(db: Session) -> tuple:
    aid = _s(db, K_APP_ID) or (os.getenv("META_APP_ID") or "").strip()
    sec = _s(db, K_APP_SECRET) or (os.getenv("META_APP_SECRET") or "").strip()
    return aid, sec


def config_id(db: Session, aid: str | None = None) -> str:
    aid = aid if aid is not None else app_creds(db)[0]
    return (_s(db, K_CONFIG_ID) or (os.getenv("META_CONFIG_ID") or "").strip()
            or KNOWN_CONFIGS.get(aid or "", ""))


def _sign(payload: str) -> str:
    from auth import SECRET_KEY
    mac = _hmac.new(str(SECRET_KEY).encode(), payload.encode(),
                    _hl.sha256).hexdigest()[:32]
    return payload + "." + mac


def make_state(user_id: int, ttl: int = 900) -> str:
    raw = f"{user_id}:{int(_time.time()) + ttl}"
    return _b64.urlsafe_b64encode(_sign(raw).encode()).decode().rstrip("=")


def check_state(state: str) -> int | None:
    try:
        pad = "=" * (-len(state) % 4)
        s = _b64.urlsafe_b64decode(state + pad).decode()
        raw, mac = s.rsplit(".", 1)
        if _sign(raw) != s:
            return None
        uid, exp = raw.split(":")
        if int(exp) < int(_time.time()):
            return None
        return int(uid)
    except Exception:
        return None


def oauth_finish(db: Session, code: str, who: str) -> dict:
    """Kod -> qisqa token -> uzoq token -> muddatsiz sahifa tokeni."""
    aid, sec = app_creds(db)
    if not (aid and sec):
        raise RuntimeError("Meta ilovasi sozlanmagan (App ID / Secret)")
    short = _get(f"{FB}/oauth/access_token", client_id=aid,
                 client_secret=sec, redirect_uri=redirect_uri(), code=code)
    st = short.get("access_token")
    if not st:
        raise RuntimeError("Facebook token bermadi")
    long_ = _get(f"{FB}/oauth/access_token", grant_type="fb_exchange_token",
                 client_id=aid, client_secret=sec, fb_exchange_token=st)
    lt = long_.get("access_token") or st
    acc = _get(f"{FB}/me/accounts",
               fields="name,access_token,instagram_business_account"
                      "{id,username,followers_count}",
               access_token=lt)
    for page in acc.get("data") or []:
        ig = page.get("instagram_business_account") or {}
        if ig.get("id") and page.get("access_token"):
            _set(db, K_TOKEN, page["access_token"], who)
            _set(db, K_USER, str(ig["id"]), who)
            _set(db, K_API, "fb", who)
            _set(db, K_NAME, ig.get("username") or page.get("name"), who)
            db.commit()
            return {"username": ig.get("username"), "page": page.get("name")}
    raise RuntimeError(
        "Ruxsat berilgan Facebook sahifalarda Instagram Business akkaunt "
        "topilmadi. Instagram Professional (Biznes) bo'lishi va Facebook "
        "sahifaga ulangan bo'lishi kerak; ruxsat oynasida sahifani "
        "belgilashni unutmang.")


@router.post("/api/smm/instagram/app")
def ig_set_app(payload: dict = Body(...), db: Session = Depends(get_db),
               user=Depends(require_role(*TOKEN_ROLES))):
    """Meta ilovasi: App ID (ochiq) va App Secret (maxfiy)."""
    aid = re.sub(r"\D", "", str(payload.get("app_id") or ""))
    sec = (payload.get("app_secret") or "").strip()
    cfg = re.sub(r"\D", "", str(payload.get("config_id") or ""))
    if len(aid) < 8:
        raise HTTPException(400, "App ID — faqat raqamlar (15-16 xonali)")
    if sec and not re.fullmatch(r"[0-9a-fA-F]{32}", sec):
        raise HTTPException(400, "App Secret 32 belgili bo'lishi kerak")
    _set(db, K_APP_ID, aid, user.full_name)
    if sec:
        _set(db, K_APP_SECRET, sec, user.full_name)
    if cfg:
        _set(db, K_CONFIG_ID, cfg, user.full_name)
    db.commit()
    audit.log(db, user, entity="integration", action="update",
              entity_label="Meta ilova",
              note=f"Meta ilova sozlandi: App ID {aid}"
                   + (f", secret {_mask(sec)}" if sec else ""))
    db.commit()
    return {"ok": True, "app_id": aid, "has_secret": bool(app_creds(db)[1])}


@router.post("/api/smm/instagram/oauth/start")
def ig_oauth_start(db: Session = Depends(get_db),
                   user=Depends(require_role(*TOKEN_ROLES))):
    aid, sec = app_creds(db)
    if not (aid and sec):
        raise HTTPException(400, "Avval Meta ilovasining App ID va App "
                                 "Secret'ini saqlang")
    q = {"client_id": aid, "redirect_uri": redirect_uri(),
         "state": make_state(user.id), "response_type": "code"}
    cfg = config_id(db, aid)
    if cfg:
        q["config_id"] = cfg          # Facebook Login for Business
    else:
        q["scope"] = OAUTH_SCOPES     # oddiy Facebook Login
    url = "https://www.facebook.com/v21.0/dialog/oauth?" + \
        urllib.parse.urlencode(q)
    return {"url": url}


@router.get(CALLBACK_PATH)
def ig_oauth_callback(code: str | None = None, state: str | None = None,
                      error: str | None = None,
                      error_description: str | None = None,
                      db: Session = Depends(get_db)):
    back = _public_base() + "/smm?tab=instagram"
    if error or not code:
        msg = error_description or error or "bekor qilindi"
        return RedirectResponse(back + "&ig_error="
                                + urllib.parse.quote(msg[:150]), 302)
    uid = check_state(state or "")
    u = db.query(models.User).get(uid) if uid else None
    if not u or u.role not in TOKEN_ROLES or not u.is_active:
        return RedirectResponse(back + "&ig_error="
                                + urllib.parse.quote("Havola eskirgan — "
                                                     "qaytadan bosing"), 302)
    try:
        info = oauth_finish(db, code, u.full_name)
    except Exception as e:
        db.rollback()
        return RedirectResponse(back + "&ig_error="
                                + urllib.parse.quote(str(e)[:200]), 302)
    try:
        audit.log(db, u, entity="integration", action="update",
                  entity_label="Instagram",
                  note=f"Instagram Facebook orqali ulandi: "
                       f"@{info.get('username')} ({info.get('page')})")
        db.commit()
    except Exception:
        db.rollback()
    try:
        _set(db, K_CURSOR, "", u.full_name)
        _set(db, K_FULL_DONE, "", u.full_name)
        db.commit()
        sync(db, who=u.full_name, full=True)
    except Exception:
        db.rollback()
    return RedirectResponse(back + "&ig=ok", 302)
