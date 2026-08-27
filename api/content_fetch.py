# -*- coding: utf-8 -*-
"""POST LINKIDAN NATIJANI AVTOMAT OLISH (2026-08-27).

Jahongir: "shu video joylangangandan keyin linkini joylashi kerak
link orqali avtomat nechta korildi nechta koment like repost
bolgani avtomat hisoboti unga korinsin."

OCHIQ AYTAMAN — HAR PLATFORMA BIR XIL EMAS:

  Telegram  ochiq kanal  -> ISHLAYDI, token kerak emas. Kanalning
                            ochiq ko'rinishidan (t.me/s/...) post
                            ko'rishlari va reaksiyalari o'qiladi.
  YouTube                -> ISHLAYDI, token kerak emas. Video
                            sahifasidan ko'rish, like va izoh soni.
  Instagram              -> FAQAT token bilan. Instagram ochiq
                            sahifadan raqam bermaydi (login
                            so'raydi). INSTAGRAM_TOKEN va
                            INSTAGRAM_USER_ID muhit o'zgaruvchilari
                            qo'yilsa, o'z postlarimiz raqamlari
                            rasmiy Graph API'dan olinadi.
  TikTok                 -> OCHIQ API YO'Q. Qo'lda kiritiladi.

Shuning uchun har javobda "note" bo'ladi: olinmasa NEGA olinmagani
aniq yoziladi. Jim turgan xato eng yomoni — SMM "ishlamayapti" deb
o'ylab, sababini bilmay qoladi.

MUHIM: bu modul faqat O'QIYDI. Hech qayerga hech narsa yozmaydi,
hech qanday hisobga kirmaydi.
"""
import os
import re
import json
import urllib.request

UA = {"User-Agent": "Mozilla/5.0 (compatible; JonyCRM/1.0)",
      "Accept-Language": "en-US,en;q=0.9"}

EMPTY = {"views": 0, "likes": 0, "comments": 0, "shares": 0,
         "saves": 0, "reach": 0}


def platform_of(url: str) -> str:
    u = (url or "").lower()
    if "t.me/" in u or "telegram.me/" in u:
        return "telegram"
    if "youtube.com" in u or "youtu.be" in u:
        return "youtube"
    if "instagram.com" in u:
        return "instagram"
    if "tiktok.com" in u:
        return "tiktok"
    if "facebook.com" in u or "fb.watch" in u:
        return "facebook"
    return "other"


def _get(url: str, timeout: int = 15) -> str:
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", "ignore")


_THOUSANDS = re.compile(r"^\d{1,3}(?:[ \u00a0\u202f,.]\d{3})+$")


def _num(text: str) -> int:
    """'1.2K', '3,4 mln', '12 345', '1,234' -> butun son.

    Ajratgichning MA'NOSI ikki xil: "12 345" da probel mingliklarni
    ajratadi, "1.2K" da nuqta kasrni bildiradi. Avval ikkalasi bir
    xil ko'rilgan edi va "12 345" dan 12 chiqardi — test tutdi.
    Endi avval mingliklar shakli tekshiriladi.
    """
    if text is None:
        return 0
    t = str(text).strip()
    core = re.match(r"[\d\s\u00a0\u202f,.]+", t)
    head = (core.group(0) if core else "").strip()
    if head and _THOUSANDS.match(head):
        return int(re.sub(r"\D", "", head))
    t = re.sub(r"[\u00a0\u202f]", " ", t).replace(",", ".")
    m = re.search(r"([\d.]+)\s*([KMB]|ming|mln|\u0442\u044b\u0441|"
                  r"\u043c\u043b\u043d)?", t, re.I)
    if not m:
        return 0
    try:
        v = float(m.group(1))
    except ValueError:
        return 0
    suf = (m.group(2) or "").lower()
    mult = {"k": 1e3, "ming": 1e3, "\u0442\u044b\u0441": 1e3,
            "m": 1e6, "mln": 1e6, "\u043c\u043b\u043d": 1e6,
            "b": 1e9}.get(suf, 1)
    return int(v * mult)


# =================================================================
#  TELEGRAM — ochiq kanal
# =================================================================

def _telegram(url: str) -> tuple:
    m = re.search(r"t(?:elegram)?\.me/(?:s/)?([A-Za-z0-9_]+)/(\d+)", url)
    if not m:
        return None, ("Telegram havolasi tushunarsiz. "
                      "Namuna: https://t.me/JonyAcademy/128")
    chan, pid = m.group(1), m.group(2)
    try:
        html = _get(f"https://t.me/{chan}/{pid}?embed=1&mode=tme")
    except Exception as e:
        return None, f"Telegram sahifasi ochilmadi: {e}"

    out = dict(EMPTY)
    v = re.search(r'class="tgme_widget_message_views"[^>]*>([^<]+)<', html)
    if v:
        out["views"] = _num(v.group(1))
    # Reaksiyalar (like o'rnida) — hammasi qo'shiladi
    react = sum(_num(x) for x in re.findall(
        r'class="tgme_widget_message_reaction[^"]*"[^>]*>.*?'
        r'<span class="[^"]*counter[^"]*">([^<]+)<', html, re.S))
    out["likes"] = react
    if not out["views"]:
        return None, ("Kanal yopiq bo'lsa Telegram raqam bermaydi. "
                      "Ochiq kanalda ishlaydi.")
    return out, "Telegram ochiq sahifasidan olindi"


# =================================================================
#  YOUTUBE
# =================================================================

def _youtube(url: str) -> tuple:
    m = re.search(r"(?:v=|youtu\.be/|/shorts/|/embed/)([A-Za-z0-9_-]{6,})",
                  url)
    if not m:
        return None, "YouTube havolasidan video raqami topilmadi"
    vid = m.group(1)
    key = (os.getenv("YOUTUBE_API_KEY") or "").strip()
    if key:
        try:
            raw = _get("https://www.googleapis.com/youtube/v3/videos"
                       f"?part=statistics&id={vid}&key={key}")
            st = (json.loads(raw).get("items") or [{}])[0].get(
                "statistics", {})
            return ({**EMPTY,
                     "views": int(st.get("viewCount") or 0),
                     "likes": int(st.get("likeCount") or 0),
                     "comments": int(st.get("commentCount") or 0)},
                    "YouTube rasmiy API'sidan olindi")
        except Exception:
            pass    # kalit ishlamasa ochiq sahifaga o'tamiz
    try:
        html = _get(f"https://www.youtube.com/watch?v={vid}")
    except Exception as e:
        return None, f"YouTube sahifasi ochilmadi: {e}"
    out = dict(EMPTY)
    v = re.search(r'"viewCount"\s*:\s*"?(\d+)"?', html)
    if v:
        out["views"] = int(v.group(1))
    lk = re.search(r'"likeCount"\s*:\s*"?(\d+)"?', html)
    if lk:
        out["likes"] = int(lk.group(1))
    cm = re.search(r'"commentCount"\s*:\s*\{"simpleText":"([\d.,KMB ]+)"',
                   html)
    if cm:
        out["comments"] = _num(cm.group(1))
    if not out["views"]:
        return None, "YouTube sahifasidan raqam o'qilmadi"
    return out, "YouTube ochiq sahifasidan olindi"


# =================================================================
#  INSTAGRAM — faqat rasmiy token bilan
# =================================================================

def _instagram(url: str) -> tuple:
    token = (os.getenv("INSTAGRAM_TOKEN") or "").strip()
    user = (os.getenv("INSTAGRAM_USER_ID") or "").strip()
    if not (token and user):
        return None, ("Instagram raqamlarini faqat rasmiy token bilan "
                      "olish mumkin. Vercel'da INSTAGRAM_TOKEN va "
                      "INSTAGRAM_USER_ID qo'shilsa avtomat ishlaydi. "
                      "Hozircha qo'lda kiriting.")
    m = re.search(r"instagram\.com/(?:p|reel|tv)/([A-Za-z0-9_-]+)", url)
    if not m:
        return None, "Instagram havolasi tushunarsiz"
    code = m.group(1)
    try:
        raw = _get("https://graph.facebook.com/v20.0/"
                   f"{user}/media?fields=id,permalink,like_count,"
                   f"comments_count&limit=100&access_token={token}")
        rows = json.loads(raw).get("data", [])
    except Exception as e:
        return None, f"Instagram API javob bermadi: {e}"
    hit = next((r for r in rows if code in (r.get("permalink") or "")), None)
    if not hit:
        return None, ("Bu post akkauntimizning oxirgi 100 tasi ichida "
                      "topilmadi")
    out = {**EMPTY,
           "likes": int(hit.get("like_count") or 0),
           "comments": int(hit.get("comments_count") or 0)}
    try:
        ins = json.loads(_get(
            f"https://graph.facebook.com/v20.0/{hit['id']}/insights"
            f"?metric=reach,saved,shares,plays&access_token={token}"))
        for it in ins.get("data", []):
            val = (it.get("values") or [{}])[0].get("value") or 0
            nm = it.get("name")
            if nm == "reach":
                out["reach"] = int(val)
            elif nm == "saved":
                out["saves"] = int(val)
            elif nm == "shares":
                out["shares"] = int(val)
            elif nm == "plays":
                out["views"] = int(val)
    except Exception:
        pass
    return out, "Instagram rasmiy API'sidan olindi"


def fetch(url: str) -> tuple:
    """(raqamlar|None, izoh) qaytaradi. Hech qachon xato tashlamaydi."""
    url = (url or "").strip()
    if not url:
        return None, "Havola kiritilmagan"
    p = platform_of(url)
    try:
        if p == "telegram":
            return _telegram(url)
        if p == "youtube":
            return _youtube(url)
        if p == "instagram":
            return _instagram(url)
        if p == "tiktok":
            return None, ("TikTok ochiq API bermaydi — raqamlarni "
                          "qo'lda kiriting.")
        if p == "facebook":
            return None, ("Facebook uchun sahifa tokeni kerak — "
                          "hozircha qo'lda kiriting.")
        return None, "Bu havola qaysi platformadan ekani aniqlanmadi"
    except Exception as e:                      # kutilmagan holat
        return None, f"Xatolik: {str(e)[:120]}"
