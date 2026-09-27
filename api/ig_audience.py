"""Instagram AUDITORIYA statistikasi (2026-09-27).

Jahongir: "Alohida SMM ichida statistikalarni ham Instagram beradiganlarni
bor jins bo'yicha, yosh guruhi, qayerdan kuzatishlar, foydalanuvchilar
aktiv paytlar, to'liq instagramdagi barcha statistikalarni eng oson
tushunadigan va chiroyli vizual animatsiya chartlar bilan qilib bergin
SMM managerimiz ko'rib mazza qivorsin".

Manba — Instagram Graph API (instagram_manage_insights):
  * follower_demographics  (jins, yosh, shahar, davlat)
  * online_followers       (obunachilar soatlar bo'yicha qachon onlayn)
  * reach / follower_count (kunlik, oxirgi 28 kun)
  * reach, views, accounts_engaged, total_interactions, likes,
    comments, shares, saves, profile_links_taps (28 kun jami)
  * follows_and_unfollows  (28 kunda kelgan va ketgan obunachi)
Plus o'zimizning bazamizdagi postlar (ig_media): qaysi soatda joylangan
post ko'proq qamrov oladi, reels va rasm solishtirmasi, top postlar,
"eng ko'p obunachi kelgan kunlar va o'sha kuni chiqqan postlar".

MUHIM: Meta reels uchun "follows" (shu videodan obuna) raqamini API
orqali BERMAYDI — faqat rasm/karusel postlar uchun beradi. Shuning uchun
reels'ning obuna ta'siri kunlik obunachi o'sishi orqali ko'rsatiladi.

Har ko'rsatkich alohida so'raladi — biri rad etilsa qolganlari ishlaydi
(xatolar "errors"da qaytadi, sahifada ko'rinmaydi). Natija 6 soat
keshlanadi: Meta limitlari va Vercel 30 s chegarasi uchun.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import json
import time
from collections import defaultdict
from datetime import date, datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

import models
import roles
import ig_connect as ig
from auth import require_role
from database import get_db

router = APIRouter()

K_CACHE = "instagram_audience_cache"
# Kesh formati o'zgarsa raqam oshiriladi — eski kesh darrov yangilanadi
CACHE_V = 2
TTL_S = 6 * 3600
TASHKENT = 5          # UTC+5, yozgi vaqt yo'q
BUDGET_S = 20.0

GENDER = {"F": "Ayollar", "M": "Erkaklar", "U": "Ko'rsatilmagan"}


def _pacific_offset(d: datetime) -> int:
    """AQSh Tinch okeani vaqti (Meta online_followers soatlari shu
    zonada): mart 2-yakshanbadan noyabr 1-yakshanbagacha -7, aks -8."""
    y = d.year
    mar = date(y, 3, 1)
    dst_start = mar + timedelta(days=(6 - mar.weekday()) % 7 + 7)
    nov = date(y, 11, 1)
    dst_end = nov + timedelta(days=(6 - nov.weekday()) % 7)
    return -7 if dst_start <= d.date() < dst_end else -8


def _breakdown(r: dict | None) -> list:
    try:
        res = r["data"][0]["total_value"]["breakdowns"][0]["results"]
    except Exception:
        return []
    out = []
    for x in res:
        dv = x.get("dimension_values") or [""]
        out.append({"key": str(dv[0]), "value": int(x.get("value") or 0)})
    out.sort(key=lambda z: -z["value"])
    return out


def _series(r: dict | None) -> list:
    """Kunlik qiymatlar. Meta end_time — kun TUGAGAN payt, shuning
    uchun sana bir kun oldinga suriladi."""
    try:
        vals = r["data"][0]["values"]
    except Exception:
        return []
    out = []
    for v in vals:
        et = (v.get("end_time") or "")[:10]
        try:
            d = (date.fromisoformat(et) - timedelta(days=1)).isoformat()
        except ValueError:
            d = et
        out.append({"date": d, "value": int(v.get("value") or 0)})
    return out


def _online(r: dict | None) -> list:
    """24 soat bo'yicha o'rtacha onlayn obunachi (Toshkent vaqtida)."""
    try:
        vals = r["data"][0]["values"]
    except Exception:
        return []
    sums = defaultdict(float)
    cnt = defaultdict(int)
    for v in vals:
        hours = v.get("value") or {}
        if not isinstance(hours, dict) or not hours:
            continue
        try:
            et = datetime.strptime((v.get("end_time") or "")[:10], "%Y-%m-%d")
        except ValueError:
            et = datetime.utcnow()
        shift = TASHKENT - _pacific_offset(et)
        for h, n in hours.items():
            try:
                hh = (int(h) + shift) % 24
            except ValueError:
                continue
            sums[hh] += float(n or 0)
            cnt[hh] += 1
    if not cnt:
        return []
    return [int(round(sums[h] / cnt[h])) if cnt[h] else 0 for h in range(24)]


def _totals(r: dict | None) -> dict:
    out = {}
    for it in (r or {}).get("data") or []:
        v = (it.get("total_value") or {}).get("value")
        if v is not None:
            out[it.get("name")] = int(v or 0)
    return out


TOTAL_METRICS = ("reach", "views", "accounts_engaged", "total_interactions",
                 "likes", "comments", "shares", "saves", "profile_links_taps")


def fetch_from_meta(db: Session) -> dict:
    tok, uid, api = ig.creds(db)
    if not tok or not uid:
        return {"ok": False, "note": "Instagram ulanmagan"}
    base = ig._base(api)
    t0 = time.time()
    errors: dict = {}

    def call(name, path, **params):
        if time.time() - t0 > BUDGET_S:
            errors[name] = "vaqt yetmadi"
            return None
        try:
            return ig._get(f"{base}/{path}", access_token=tok, **params)
        except Exception as e:
            errors[name] = str(e)[:200]
            return None

    out: dict = {"ok": True}
    prof = call("profile", uid,
                fields="username,name,followers_count,follows_count,"
                       "media_count,profile_picture_url") or {}
    if not prof:
        # Akkauntning o'zi ham kelmadi — Meta ishlamayapti yoki token
        # eskirgan. Eski keshni buzmaslik uchun muvaffaqiyatsiz deymiz.
        return {"ok": False, "note": "Instagram javob bermadi: "
                + errors.get("profile", "")[:150], "errors": errors}
    out["profile"] = {k: prof.get(k) for k in (
        "username", "name", "followers_count", "follows_count",
        "media_count", "profile_picture_url")}

    for bd in ("gender", "age", "city", "country"):
        out[bd] = _breakdown(call(
            f"demo_{bd}", f"{uid}/insights", metric="follower_demographics",
            period="lifetime", metric_type="total_value", breakdown=bd))

    now = datetime.utcnow()
    until = int(now.timestamp())
    since = int((now - timedelta(days=28)).timestamp())

    # online_followers: since/until berilmasa Meta faqat oxirgi 1-2 kunni
    # qaytaradi, ular esa odatda hali BO'SH ({}). Shuning uchun 29 kunlik
    # oraliq so'raymiz; baribir bo'sh bo'lsa — oraliqsiz qayta.
    oh = _online(call(
        "online", f"{uid}/insights", metric="online_followers",
        period="lifetime",
        since=int((now - timedelta(days=29)).timestamp()), until=until))
    if not oh:
        oh = _online(call("online_2", f"{uid}/insights",
                          metric="online_followers", period="lifetime"))
    if not oh and "online" not in errors:
        errors["online"] = "Meta onlayn soatlarni bo'sh qaytardi"
    out["online_hours"] = oh
    out["reach_daily"] = _series(call(
        "reach_daily", f"{uid}/insights", metric="reach", period="day",
        since=since, until=until))
    out["followers_daily"] = _series(call(
        "followers_daily", f"{uid}/insights", metric="follower_count",
        period="day", since=since, until=until))

    tot = _totals(call("totals", f"{uid}/insights",
                       metric=",".join(TOTAL_METRICS), period="day",
                       metric_type="total_value", since=since, until=until))
    if not tot:
        # Birortasi rad etilsa butun so'rov yiqiladi — alohida so'raymiz
        for m in TOTAL_METRICS:
            tot.update(_totals(call(f"total_{m}", f"{uid}/insights",
                                    metric=m, period="day",
                                    metric_type="total_value",
                                    since=since, until=until)))
    out["totals"] = tot

    fu = _breakdown(call("follows_unfollows", f"{uid}/insights",
                         metric="follows_and_unfollows", period="day",
                         metric_type="total_value", breakdown="follow_type",
                         since=since, until=until))
    fmap = {x["key"].upper(): x["value"] for x in fu}
    out["follows"] = fmap.get("FOLLOWER")
    out["unfollows"] = fmap.get("NON_FOLLOWER")
    out["errors"] = errors
    out["v"] = CACHE_V
    out["fetched_at"] = now.isoformat(timespec="seconds")
    return out


# ------------------------------------------------ o'zimizning postlardan
def _local(db: Session, followers_daily: list) -> dict:
    now = datetime.utcnow()
    rows = (db.query(models.IgMedia)
            .filter(models.IgMedia.posted_at >= now - timedelta(days=180))
            .all())
    by_hour = defaultdict(list)
    by_wd = defaultdict(list)
    by_type = defaultdict(list)
    by_day = defaultdict(list)
    for m in rows:
        loc = m.posted_at + timedelta(hours=TASHKENT)
        r = int(m.reach or 0)
        by_hour[loc.hour].append(r)
        by_wd[loc.weekday()].append(r)
        t = (m.media_type or "").upper()
        kind = ("Reels / video" if t == "VIDEO" else
                "Karusel" if t == "CAROUSEL_ALBUM" else "Rasm")
        by_type[kind].append(m)
        by_day[loc.date().isoformat()].append(m)

    def avg(xs):
        return int(sum(xs) / len(xs)) if xs else 0

    post_hours = [{"hour": h, "avg_reach": avg(by_hour.get(h, [])),
                   "posts": len(by_hour.get(h, []))} for h in range(24)]
    wd_names = ["Du", "Se", "Ch", "Pa", "Ju", "Sh", "Ya"]
    post_weekdays = [{"day": wd_names[i], "avg_reach": avg(by_wd.get(i, [])),
                      "posts": len(by_wd.get(i, []))} for i in range(7)]
    types = []
    for k, ms in by_type.items():
        n = len(ms)
        eng = sum(int(x.likes or 0) + int(x.comments or 0) + int(x.saves or 0)
                  + int(x.shares or 0) for x in ms)
        types.append({"type": k, "posts": n,
                      "avg_views": avg([int(x.views or 0) for x in ms]),
                      "avg_reach": avg([int(x.reach or 0) for x in ms]),
                      "avg_engagement": int(eng / n) if n else 0})
    types.sort(key=lambda z: -z["avg_views"])

    last30 = [m for m in rows if m.posted_at >= now - timedelta(days=30)]

    def card(m):
        cap = (m.caption or "").strip().splitlines()[0][:80] if m.caption else ""
        return {"id": m.id, "caption": cap or m.media_type or "Post",
                "permalink": m.permalink, "type": m.media_type,
                "posted_at": m.posted_at.isoformat() if m.posted_at else None,
                "views": int(m.views or 0), "reach": int(m.reach or 0),
                "likes": int(m.likes or 0), "shares": int(m.shares or 0),
                "saves": int(m.saves or 0), "follows": int(m.follows or 0)}

    top_views = [card(m) for m in
                 sorted(last30, key=lambda x: -(x.views or 0))[:5]]
    top_follows = [card(m) for m in sorted(
        [m for m in rows if (m.follows or 0) > 0],
        key=lambda x: -(x.follows or 0))[:5]]
    # Kunlik obunachi o'sishi + o'sha kuni chiqqan postlar (reels'ning
    # obuna ta'sirini ko'rish uchun yagona halol yo'l)
    growth_days = []
    for d in followers_daily or []:
        posts = by_day.get(d["date"], [])
        growth_days.append({"date": d["date"], "new_followers": d["value"],
                            "posts": [card(m) for m in posts][:3]})
    best_days = sorted([g for g in growth_days if g["posts"]],
                       key=lambda g: -g["new_followers"])[:5]
    return {"post_hours": post_hours, "post_weekdays": post_weekdays,
            "types": types, "top_views": top_views,
            "top_follows": top_follows, "growth_days": growth_days,
            "best_days": best_days, "posts_180d": len(rows)}


def _pct(part, whole):
    return round(100.0 * part / whole) if whole else 0


def _insights_text(meta: dict, loc: dict) -> list:
    tips = []
    g = meta.get("gender") or []
    tot_g = sum(x["value"] for x in g)
    if g and tot_g:
        top = g[0]
        tips.append({"icon": "👥", "text": f"Obunachilarning {_pct(top['value'], tot_g)}% — "
                     f"{GENDER.get(top['key'], top['key']).lower()}."})
    a = meta.get("age") or []
    tot_a = sum(x["value"] for x in a)
    if a and tot_a:
        tips.append({"icon": "🎂", "text": f"Eng katta yosh guruhi: {a[0]['key']} yosh "
                     f"({_pct(a[0]['value'], tot_a)}%). Kontent tili va mavzusini "
                     "shu yoshga moslang."})
    c = meta.get("city") or []
    tot_c = sum(x["value"] for x in c)
    if c and tot_c:
        tips.append({"icon": "📍", "text": f"Eng ko'p obunachi: {c[0]['key'].split(',')[0]} "
                     f"({_pct(c[0]['value'], tot_c)}%)."})
    oh = meta.get("online_hours") or []
    if oh and max(oh) > 0:
        h = max(range(24), key=lambda i: oh[i])
        tips.append({"icon": "⏰", "text": f"Obunachilar eng faol payt: {h:02d}:00–{(h + 1) % 24:02d}:00. "
                     f"Postni undan 30–60 daqiqa oldin joylang."})
    ph = [x for x in loc.get("post_hours") or [] if x["posts"] >= 3]
    if ph:
        b = max(ph, key=lambda x: x["avg_reach"])
        tips.append({"icon": "🚀", "text": f"Sizning postlaringiz {b['hour']:02d}:00 atrofida "
                     f"joylanganda o'rtacha qamrov eng yuqori ({b['avg_reach']:,}).".replace(",", " ")})
    ty = loc.get("types") or []
    if len(ty) >= 2 and ty[-1]["avg_views"]:
        x = ty[0]["avg_views"] / max(ty[-1]["avg_views"], 1)
        if x >= 1.3:
            tips.append({"icon": "🎬", "text": f"{ty[0]['type']} {ty[-1]['type'].lower()}ga qaraganda "
                         f"{x:.1f} barobar ko'p ko'riladi."})
    fol, unf = meta.get("follows"), meta.get("unfollows")
    if fol is not None:
        net = (fol or 0) - (unf or 0)
        tips.append({"icon": "📈", "text": f"28 kunda {fol} kishi obuna bo'ldi"
                     + (f", {unf} kishi chiqib ketdi — sof o'sish {net:+d}." if unf is not None else ".")})
    bd = loc.get("best_days") or []
    if bd and bd[0]["new_followers"] > 0:
        p = bd[0]["posts"][0]["caption"] if bd[0]["posts"] else ""
        tips.append({"icon": "⭐", "text": f"Eng ko'p obunachi kelgan kun: {bd[0]['date']} "
                     f"(+{bd[0]['new_followers']}). O'sha kuni: «{p[:50]}»."})
    return tips


@router.get("/api/smm/instagram/audience")
def ig_audience(refresh: int = 0, db: Session = Depends(get_db),
                user=Depends(require_role(*roles.SMM_ACCESS))):
    cached = None
    raw = ig._s(db, K_CACHE)
    if raw:
        try:
            cached = json.loads(raw)
        except ValueError:
            cached = None
    fresh = False
    if cached and not refresh:
        try:
            age = (datetime.utcnow() - datetime.fromisoformat(
                cached.get("fetched_at"))).total_seconds()
            fresh = age < TTL_S and cached.get("v") == CACHE_V
        except Exception:
            fresh = False
    meta = cached if (cached and fresh) else None
    if meta is None:
        meta = fetch_from_meta(db)
        if meta.get("ok"):
            ig._set(db, K_CACHE, json.dumps(meta, ensure_ascii=False),
                    getattr(user, "full_name", None))
            db.commit()
        elif cached:
            meta = cached            # Meta javob bermasa eski natija
    loc = _local(db, meta.get("followers_daily") or [])
    return {**meta, "local": loc, "tips": _insights_text(meta, loc)}
