"""JONY ACADEMY TELEGRAM BOTI — JonyOS ichida, tekin (2026-10-13).

Jahongir: "railwayga ulangan jonyacademybot o'chib qolibdi ... botni
boshqa tekin joydan ishga tushir".

Bot ilgari Railway'da polling bilan ishlardi; Railway trial tugab
24-sentabrda hamma servislar o'chirildi. Endi bot WEBHOOK: Telegram
har xabarni jonyos.uz/api/tg/academy-bot/<sir> ga yuboradi, Vercel
uni shu modulda qayta ishlaydi. Alohida server kerak emas, uxlamaydi,
pul ham ketmaydi.

Oqim eski bot bilan bir xil (matnlar ham): ism -> telefon (kontakt
tugmasi) -> yosh/sinf -> kurs -> filial -> tasdiqlash. Farqi:
  * suhbat holati xotirada emas, bazada (academy_bot_sessions);
  * har murojaat JonyOS'da LID bo'lib tushadi (manba: telegram,
    tanlangan filialga) va filial adminlariga vazifa ochiladi;
  * sotuv guruhiga xabar + "Qo'ng'iroq qilindi / Keldi / Kelmadi"
    tugmalari avvalgidek; /stat, /royxat, /broadcast faqat adminlarga;
  * kunlik hisobot 20:00 da (Toshkent) /api/health cron'i orqali.

Sozlamalar (Vercel Environment Variables):
  ACADEMY_BOT_TOKEN       — BotFather tokeni (majburiy)
  ACADEMY_SALES_GROUP_ID  — sotuv guruhi chat ID (ixtiyoriy)
  ACADEMY_ADMIN_IDS       — vergul bilan admin Telegram ID'lari
Token kodda ham, javoblarda ham hech qachon ko'rinmaydi.
"""
import csv
import hashlib
import html
import io
import json
import os
import re
import urllib.request
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

import models
import roles
from auth import require_role
from database import get_db

router = APIRouter()

KURSLAR = ["Ingliz tili", "Rus tili", "Turk tili", "Nemis tili"]
FILIALLAR = ["Zafar", "Bekobod Shahar", "Stretinko"]
FILIAL_KONTAKT = {
    "Zafar": {
        "phones": ["+998941326565", "+998931126565"],
        "usernames": ["@Jonyacademyadmin", "@Jony_Academy_admin"],
    },
    "Bekobod Shahar": {
        "phones": ["+998772769777", "+998948697797"],
        "usernames": ["@jonyAcademybekobod", "@Bekobod_Admin_2"],
    },
    "Stretinko": {
        "phones": ["+998773759777"],
        "usernames": ["@Jony_Admin_Stretinka"],
    },
}
STATUS_LABELS = {
    "called": "📞 Qo'ng'iroq qilindi",
    "came": "✅ Keldi",
    "not_came": "❌ Kelmadi",
}
CONTACT_BTN = "📱 Raqamni avtomatik yuborish"
YES, NO = "✅ Tasdiqlash", "❌ Bekor qilish"


# ─── Sozlamalar va Telegram API ─────────────────────────────────────────

def _token() -> str:
    return os.environ.get("ACADEMY_BOT_TOKEN", "").strip()


def _sales_group() -> str:
    return os.environ.get("ACADEMY_SALES_GROUP_ID", "").strip()


def _admin_ids() -> set:
    raw = os.environ.get("ACADEMY_ADMIN_IDS", "")
    return {x.strip() for x in raw.split(",")
            if x.strip().lstrip("-").isdigit()}


def enabled() -> bool:
    return bool(_token())


def webhook_secret() -> str:
    """Manzil va X-Telegram-Bot-Api-Secret-Token uchun: tokendan
    chiqarilgan, taxmin qilib bo'lmaydigan qisqa imzo."""
    return hashlib.sha256(("academy:" + _token()).encode()).hexdigest()[:32]


# Testlarda Telegram'ga borilmaydi — chaqiruvlar shu ro'yxatga yoziladi
_SENT: list = []
TEST_MODE = False


def tg(method: str, payload: dict, timeout: int = 8):
    """Telegram Bot API. Xato bo'lsa None — hech qachon raise qilmaydi."""
    if TEST_MODE:
        _SENT.append((method, payload))
        if method == "sendMessage":
            return {"ok": True, "result": {"message_id": len(_SENT)}}
        return {"ok": True, "result": True}
    tok = _token()
    if not tok:
        return None
    try:
        req = urllib.request.Request(
            f"https://api.telegram.org/bot{tok}/{method}",
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode())
    except Exception:
        return None


def _send(chat_id, text: str, markup=None, parse_mode="HTML", **extra):
    p = {"chat_id": str(chat_id), "text": text}
    if parse_mode:
        p["parse_mode"] = parse_mode
    if markup is not None:
        p["reply_markup"] = markup
    p.update(extra)
    return tg("sendMessage", p)


def _send_document(chat_id, filename: str, blob: bytes, caption: str = ""):
    if TEST_MODE:
        _SENT.append(("sendDocument", {"chat_id": str(chat_id),
                                       "filename": filename,
                                       "caption": caption}))
        return True
    tok = _token()
    if not tok:
        return False
    boundary = "----JonyAcademy" + os.urandom(8).hex()
    nl = b"\r\n"
    body = io.BytesIO()
    for name, value in (("chat_id", chat_id), ("caption", caption[:1000])):
        body.write(b"--" + boundary.encode() + nl)
        body.write(f'Content-Disposition: form-data; name="{name}"'
                   .encode() + nl + nl + str(value).encode() + nl)
    body.write(b"--" + boundary.encode() + nl)
    body.write(f'Content-Disposition: form-data; name="document"; '
               f'filename="{filename}"'.encode() + nl)
    body.write(b"Content-Type: text/csv" + nl + nl + blob + nl)
    body.write(b"--" + boundary.encode() + b"--" + nl)
    try:
        req = urllib.request.Request(
            f"https://api.telegram.org/bot{tok}/sendDocument",
            data=body.getvalue(),
            headers={"Content-Type":
                     f"multipart/form-data; boundary={boundary}"})
        with urllib.request.urlopen(req, timeout=30) as r:
            return bool(json.loads(r.read().decode()).get("ok"))
    except Exception:
        return False


def _e(v):
    """HTML qochirish; apostrof (Qo'ng'iroq) buzilmasin."""
    return html.escape(str(v), quote=False)


REMOVE_KB = {"remove_keyboard": True}


def _contact_kb():
    return {"keyboard": [[{"text": CONTACT_BTN, "request_contact": True}]],
            "resize_keyboard": True, "one_time_keyboard": True}


# ─── Telefon ─────────────────────────────────────────────────────────────

def validate_phone(phone: str) -> bool:
    p = phone.strip().replace(" ", "").replace("-", "")
    return bool(re.match(r'^(\+998|998|0)[0-9]{9}$|^[0-9]{9}$', p))


def normalize_phone(phone: str) -> str:
    p = phone.strip().replace(" ", "").replace("-", "")
    if p.startswith("+998"):
        return p
    if p.startswith("998"):
        return "+" + p
    if p.startswith("0") and len(p) == 10:
        return "+998" + p[1:]
    if len(p) == 9:
        return "+998" + p
    return phone


# ─── Suhbat holati ───────────────────────────────────────────────────────

def _get_session(db: Session, chat_id: str):
    s = db.query(models.AcademyBotSession).get(str(chat_id))
    if s is None:
        s = models.AcademyBotSession(chat_id=str(chat_id), state=None,
                                     data_json="{}")
        db.add(s)
    try:
        data = json.loads(s.data_json or "{}")
    except Exception:
        data = {}
    return s, data


def _save(db: Session, s, state, data):
    s.state = state
    s.data_json = json.dumps(data, ensure_ascii=False)
    s.updated_at = datetime.utcnow()
    db.commit()


def _now_local():
    return roles.to_local(datetime.utcnow())


# ─── JonyOS lidi ─────────────────────────────────────────────────────────

def _match_branch(db: Session, name: str):
    """"Bekobod Shahar" -> "Bekobod 1" kabi: sayt formasidagi bilan bir
    xil qoida (aniq moslik, bo'lmasa birinchi so'z bo'yicha)."""
    nm = (name or "").lower().strip()
    if not nm:
        return None
    all_b = db.query(models.Branch).order_by(models.Branch.id).all()
    b = next((x for x in all_b if (x.name or "").lower() == nm), None)
    if b is None:
        head = nm.split()[0]
        b = next((x for x in all_b
                  if (x.name or "").lower().startswith(head)), None)
    return b


def _create_lead(db: Session, d: dict, username: str):
    """Murojaatni JonyOS'ga lid qilib yozadi. Xato bo'lsa None —
    bot baribir murojaatni qabul qiladi va guruhga yuboradi."""
    try:
        from common import _ensure_public_id, _hr_task
        branch = _match_branch(db, d.get("branch"))
        tail = re.sub(r"\D", "", d.get("phone") or "")[-9:]
        since = datetime.utcnow() - timedelta(hours=24)
        for l in (db.query(models.Lead)
                  .filter(models.Lead.created_at >= since).all()):
            dg = re.sub(r"\D", "", l.phone or "")
            if dg and dg[-9:] == tail:
                return l
        note = [
            "Telegram bot orqali ariza (Jony Academy bot)",
            f"Yo'nalish: {d.get('course')}",
            f"Yosh/sinf: {d.get('grade')}",
            f"Tanlagan filiali: {d.get('branch')}",
        ]
        if username:
            note.append(f"Telegram: @{username}")
        lead = models.Lead(
            full_name=(d.get("name") or "")[:120],
            phone=d.get("phone"),
            source="telegram",
            stage=roles.LEAD_SOURCE_DEFAULT_STAGE.get("telegram", "new"),
            branch_id=branch.id if branch else None,
            note="\n".join(note),
            created_by="Jony Academy bot")
        db.add(lead)
        db.commit()
        db.refresh(lead)
        _ensure_public_id(db, "lead", lead)
        db.commit()
        try:
            _hr_task(db,
                     title=f"Botdan ariza: {lead.full_name} "
                           f"({lead.public_id or lead.id})",
                     body="\n".join(note) + f"\nTelefon: {lead.phone}\n"
                          "Iltimos, bugunning o'zida qo'ng'iroq qiling.",
                     to_roles=[roles.ADMINISTRATOR, roles.SALES_MANAGER,
                               roles.SALES_HEAD, roles.BRANCH_MANAGER],
                     branch_id=lead.branch_id, days=1, priority="high")
            db.commit()
        except Exception:
            db.rollback()
        return lead
    except Exception:
        db.rollback()
        return None


# ─── Ro'yxatdan o'tish oqimi ─────────────────────────────────────────────

def _start(db, s, chat_id):
    _send(chat_id,
          "👋 Salom! <b>Jony Academy</b> ga xush kelibsiz!\n\n"
          "Ro'yxatdan o'tish uchun <b>to'liq ismingizni</b> kiriting:",
          REMOVE_KB)
    _save(db, s, "name", {})


def _cancel(db, s, chat_id):
    _send(chat_id,
          "❌ Bekor qilindi.\n/start orqali qayta boshlashingiz mumkin.",
          REMOVE_KB)
    _save(db, s, None, {})


def _ask_phone(db, s, data, chat_id, text):
    data["name"] = text.strip()[:120]
    _send(chat_id,
          "📱 <b>Telefon raqamingizni</b> yuboring:\n\n"
          "🔘 Quyidagi tugmani bosing — Telegram raqamingizni o'zi yuboradi\n"
          "✏️ Yoki qo'lda kiriting: +998901234567",
          _contact_kb())
    _save(db, s, "phone", data)


def _ask_grade(db, s, data, chat_id, msg):
    contact = msg.get("contact")
    if contact and contact.get("phone_number"):
        phone = str(contact["phone_number"])
        normalized = phone if phone.startswith("+") else "+" + phone
    else:
        phone = (msg.get("text") or "").strip()
        if not validate_phone(phone):
            _send(chat_id,
                  "❌ Telefon raqam noto'g'ri formatda!\n\n"
                  "Tugmani bosing yoki to'g'ri kiriting: +998901234567",
                  _contact_kb(), parse_mode=None)
            return
        normalized = normalize_phone(phone)
    if (db.query(models.AcademyBotReg)
            .filter(models.AcademyBotReg.phone == normalized).first()):
        _send(chat_id,
              "⚠️ Bu telefon raqam allaqachon ro'yxatdan o'tgan!\n"
              "Agar muammo bo'lsa, adminimizga murojaat qiling: @jony_academy",
              REMOVE_KB, parse_mode=None)
        _save(db, s, None, {})
        return
    data["phone"] = normalized
    _send(chat_id,
          "🎒 <b>Yoshingiz yoki nechanchi sinfda</b> o'qishingizni kiriting:\n"
          "Masalan: 14 yosh, 7-sinf",
          REMOVE_KB)
    _save(db, s, "grade", data)


def _ask_course(db, s, data, chat_id, text):
    data["grade"] = text.strip()[:80]
    kb = {"inline_keyboard": [[{"text": k, "callback_data": f"course:{k}"}]
                              for k in KURSLAR]}
    _send(chat_id, "📚 Qaysi <b>kursga</b> yozilmoqchisiz?", kb)
    _save(db, s, "course", data)


def _ask_branch(db, s, data, chat_id, cq):
    course = cq["data"].split(":", 1)[1]
    if course not in KURSLAR:
        return
    data["course"] = course
    kb = {"inline_keyboard": [[{"text": f, "callback_data": f"branch:{f}"}]
                              for f in FILIALLAR]}
    tg("editMessageText", {
        "chat_id": str(chat_id), "message_id": cq["message"]["message_id"],
        "text": f"✅ Kurs tanlandi: <b>{_e(course)}</b>\n\n"
                "📍 Qaysi <b>filialga</b> borishni xohlaysiz?",
        "parse_mode": "HTML", "reply_markup": kb})
    _save(db, s, "branch", data)


def _ask_confirm(db, s, data, chat_id, cq):
    branch = cq["data"].split(":", 1)[1]
    if branch not in FILIALLAR:
        return
    data["branch"] = branch
    e = _e
    summary = (
        "📋 <b>Ma'lumotlaringizni tekshiring:</b>\n\n"
        f"👤 Ism: {e(data.get('name', ''))}\n"
        f"📱 Telefon: {e(data.get('phone', ''))}\n"
        f"🎒 Yosh/sinf: {e(data.get('grade', ''))}\n"
        f"📚 Kurs: {e(data.get('course', ''))}\n"
        f"📍 Filial: {e(branch)}")
    tg("editMessageText", {
        "chat_id": str(chat_id), "message_id": cq["message"]["message_id"],
        "text": summary, "parse_mode": "HTML"})
    _send(chat_id, "Yuqoridagi ma'lumotlar to'g'rimi?",
          {"keyboard": [[YES, NO]], "resize_keyboard": True,
           "one_time_keyboard": True}, parse_mode=None)
    _save(db, s, "confirm", data)


def _confirm(db, s, data, chat_id, user):
    e = _e
    need = ("name", "phone", "grade", "course", "branch")
    if any(not data.get(k) for k in need):
        _start(db, s, chat_id)
        return
    username = user.get("username") or ""
    lead = _create_lead(db, data, username)
    reg = models.AcademyBotReg(
        tg_user_id=str(user.get("id") or ""), username=username,
        name=data["name"], phone=data["phone"], grade=data["grade"],
        course=data["course"], branch=data["branch"], status="pending",
        lead_id=lead.id if lead else None)
    db.add(reg)
    db.commit()
    db.refresh(reg)
    _save(db, s, None, {})

    _send(chat_id,
          "🎉 <b>Murojaatingiz muvaffaqiyatli qabul qilindi!</b>\n\n"
          f"📍 <b>{e(data['branch'])}</b> filialimiz xodimlari tez orada "
          "siz bilan bog'lanishadi.\n\n"
          "Savollar bo'lsa: @jony_academy\nKo'rishguncha! 👋",
          REMOVE_KB)
    k = FILIAL_KONTAKT.get(data["branch"])
    if k:
        phones = "\n".join(f"📞 <code>{p}</code>" for p in k["phones"])
        unames = "\n".join(f"💬 {u}" for u in k["usernames"])
        _send(chat_id,
              f"📍 <b>{e(data['branch'])}</b> filiali admini bilan "
              f"to'g'ridan-to'g'ri bog'lanish:\n\n{phones}\n{unames}\n\n"
              "Shoshilsangiz — hoziroq murojaat qilishingiz mumkin! 🚀")

    group = _sales_group()
    if group:
        uname = f"@{username}" if username else "—"
        msg = (
            "🔔 <b>YANGI MUROJAAT — Jony Academy</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 <b>Ism:</b> {e(data['name'])}\n"
            f"📱 <b>Telefon:</b> <code>{e(data['phone'])}</code>\n"
            f"🎒 <b>Yosh/sinf:</b> {e(data['grade'])}\n"
            f"📚 <b>Kurs:</b> {e(data['course'])}\n"
            f"📍 <b>Filial:</b> {e(data['branch'])}\n"
            f"💬 <b>Telegram:</b> {e(uname)}\n"
            f"🕐 <b>Vaqt:</b> {_now_local().strftime('%d.%m.%Y %H:%M')}\n"
            + (f"🗂 <b>JonyOS lid:</b> {e(lead.public_id or str(lead.id))}\n"
               if lead else "")
            + "━━━━━━━━━━━━━━━━━━━━")
        kb = {"inline_keyboard": [
            [{"text": STATUS_LABELS["called"],
              "callback_data": f"status:{reg.id}:called"},
             {"text": STATUS_LABELS["came"],
              "callback_data": f"status:{reg.id}:came"}],
            [{"text": STATUS_LABELS["not_came"],
              "callback_data": f"status:{reg.id}:not_came"}],
        ]}
        r = _send(group, msg, kb)
        if r and r.get("ok"):
            reg.group_message_id = str(r["result"].get("message_id"))
            db.commit()


def _status(db, cq):
    parts = (cq.get("data") or "").split(":")
    cq_id = cq.get("id")
    if len(parts) != 3 or not parts[1].isdigit():
        tg("answerCallbackQuery", {"callback_query_id": cq_id,
                                   "text": "Xato!"})
        return
    _, rid, st = parts
    if st not in STATUS_LABELS:
        tg("answerCallbackQuery", {"callback_query_id": cq_id,
                                   "text": "Xato!"})
        return
    reg = db.query(models.AcademyBotReg).get(int(rid))
    label = STATUS_LABELS[st]
    if reg is not None:
        reg.status = st
        reg.updated_at = datetime.utcnow()
        db.commit()
    tg("answerCallbackQuery", {"callback_query_id": cq_id,
                               "text": f"✅ {label}"})
    msg = cq.get("message") or {}
    chat_id = (msg.get("chat") or {}).get("id")
    tg("editMessageReplyMarkup", {"chat_id": str(chat_id),
                                  "message_id": msg.get("message_id"),
                                  "reply_markup": {"inline_keyboard": []}})
    who = cq.get("from") or {}
    manager = " ".join(x for x in (who.get("first_name"),
                                   who.get("last_name")) if x) or "—"
    name = reg.name if reg else "—"
    _send(chat_id,
          f"🔄 <b>{_e(name)}</b> — {_e(label)}\n"
          f"👤 {_e(manager)} · 🕐 "
          f"{_now_local().strftime('%d.%m.%Y %H:%M')}",
          reply_to_message_id=msg.get("message_id"))


# ─── Admin buyruqlari ────────────────────────────────────────────────────

def _is_admin(user_id, chat_id) -> bool:
    """Admin: ACADEMY_ADMIN_IDS dagi odam yoki sotuv guruhining o'zi.
    Eski botda /stat va /royxat hammaga ochiq edi — endi yopiq
    (ro'yxatda telefon raqamlar bor)."""
    return (str(user_id) in _admin_ids()
            or (_sales_group() and str(chat_id) == _sales_group()))


def _counts(rows):
    d = {}
    for r in rows:
        d[r] = d.get(r, 0) + 1
    return sorted(d.items(), key=lambda x: -x[1])


def _stat_text(regs, title: str, today_only=False) -> str:
    st = {}
    for r in regs:
        st[r.status or "pending"] = st.get(r.status or "pending", 0) + 1
    courses = _counts([r.course or "—" for r in regs])
    branches = _counts([r.branch or "—" for r in regs])
    return (
        f"📊 <b>{title}</b>\n━━━━━━━━━━━━━━━━━━━━\n"
        + (f"📥 Bugun: <b>{len(regs)}</b> ta murojaat\n\n" if today_only
           else f"Jami: <b>{len(regs)}</b>\n\n")
        + "📈 <b>Holat:</b>\n"
        f"  ⏳ Kutilmoqda: {st.get('pending', 0)}\n"
        f"  📞 Qo'ng'iroq qilindi: {st.get('called', 0)}\n"
        f"  ✅ Keldi: {st.get('came', 0)}\n"
        f"  ❌ Kelmadi: {st.get('not_came', 0)}\n\n"
        "📚 <b>Kurslar:</b>\n"
        + "\n".join(f"  • {_e(c)}: {n}" for c, n in courses)
        + "\n\n📍 <b>Filiallar:</b>\n"
        + "\n".join(f"  • {_e(b)}: {n}" for b, n in branches))


def _stat(db, chat_id):
    regs = db.query(models.AcademyBotReg).all()
    _send(chat_id, _stat_text(regs, "Statistika"))


def _royxat(db, chat_id):
    regs = (db.query(models.AcademyBotReg)
            .order_by(models.AcademyBotReg.id).all())
    out = io.StringIO()
    w = csv.writer(out)
    w.writerow(["ID", "Ism", "Telefon", "Yosh/sinf", "Kurs", "Filial",
                "Holat", "Ro'yxat vaqti", "Yangilangan", "Telegram",
                "JonyOS lid"])
    for r in regs:
        w.writerow([r.id, r.name, r.phone, r.grade, r.course, r.branch,
                    r.status,
                    roles.to_local(r.created_at).strftime("%Y-%m-%d %H:%M")
                    if r.created_at else "",
                    roles.to_local(r.updated_at).strftime("%Y-%m-%d %H:%M")
                    if r.updated_at else "",
                    r.username or "", r.lead_id or ""])
    fname = f"jony_academy_{_now_local().strftime('%Y%m%d_%H%M')}.csv"
    _send_document(chat_id, fname, out.getvalue().encode("utf-8-sig"),
                   caption=f"📋 Jami {len(regs)} ta murojaat")


def _broadcast_send(db, s, chat_id, text):
    """Hamma ro'yxatdan o'tganlarga xabar. Vercel funksiyasi 30
    soniyada to'xtaydi — 25 soniyadan keyin to'xtab, qolganini
    aytamiz (xabar ikki marta borib qolmasin)."""
    import time
    t0 = time.monotonic()
    ids = sorted({r.tg_user_id for r in db.query(models.AcademyBotReg)
                  .filter(models.AcademyBotReg.tg_user_id.isnot(None))
                  .all() if r.tg_user_id and r.tg_user_id != "0"})
    sent = failed = 0
    left = 0
    for i, uid in enumerate(ids):
        if time.monotonic() - t0 > 25:
            left = len(ids) - i
            break
        r = _send(uid, f"📢 Jony Academy:\n\n{text}", parse_mode=None)
        if r and r.get("ok"):
            sent += 1
        else:
            failed += 1
    _save(db, s, None, {})
    _send(chat_id,
          "✅ <b>Broadcast tugadi!</b>\n\n"
          f"📨 Yuborildi: <b>{sent}</b>\n❌ Yuborilmadi: <b>{failed}</b>"
          + (f"\n⏸ Vaqt yetmadi, yuborilmagan: <b>{left}</b>" if left else ""))


def daily_report(db, force: bool = False) -> bool:
    """20:00 (Toshkent) kunlik hisobot sotuv guruhiga. /api/health
    cron'i har 30 daqiqada chaqiradi; kuniga BIR marta yuboriladi
    (IntegrationSetting'da sana belgisi). Bugun murojaat bo'lmasa —
    yuborilmaydi (eski botdagidek)."""
    group = _sales_group()
    if not (enabled() and group):
        return False
    now = _now_local()
    if not force and now.hour != 20:
        return False
    key = "academy_bot_daily_sent"
    today = now.strftime("%Y-%m-%d")
    row = db.query(models.IntegrationSetting).get(key)
    if row is not None and row.value == today and not force:
        return False
    start_local = now.replace(hour=0, minute=0, second=0, microsecond=0)
    start_utc = start_local - timedelta(hours=roles.TIMEZONE_OFFSET_HOURS)
    regs = (db.query(models.AcademyBotReg)
            .filter(models.AcademyBotReg.created_at >= start_utc).all())
    if row is None:
        row = models.IntegrationSetting(key=key)
        db.add(row)
    row.value = today
    row.updated_by = "academy bot"
    db.commit()
    if not regs:
        return False
    total = db.query(models.AcademyBotReg).count()
    text = (_stat_text(regs, f"KUNLIK HISOBOT — {now.strftime('%d.%m.%Y')}",
                       today_only=True)
            + f"\n\n━━━━━━━━━━━━━━━━━━━━\n📊 Jami barcha vaqt: <b>{total}</b>")
    r = _send(group, text)
    return bool(r and r.get("ok"))


# ─── Yangilanishni yo'naltirish ──────────────────────────────────────────

def handle_update(db: Session, upd: dict) -> None:
    cq = upd.get("callback_query")
    if cq:
        data = cq.get("data") or ""
        if data.startswith("status:"):
            _status(db, cq)
            return
        msg = cq.get("message") or {}
        chat_id = (msg.get("chat") or {}).get("id")
        if chat_id is None:
            return
        tg("answerCallbackQuery", {"callback_query_id": cq.get("id")})
        s, d = _get_session(db, chat_id)
        if data.startswith("course:") and s.state == "course":
            _ask_branch(db, s, d, chat_id, cq)
        elif data.startswith("branch:") and s.state == "branch":
            _ask_confirm(db, s, d, chat_id, cq)
        return

    msg = upd.get("message")
    if not msg:
        return
    chat = msg.get("chat") or {}
    chat_id = chat.get("id")
    user = msg.get("from") or {}
    text = (msg.get("text") or "").strip()
    if chat_id is None:
        return
    cmd = text.split()[0].split("@")[0].lower() if text.startswith("/") else ""

    # Guruhlarda faqat admin buyruqlari ishlaydi — bot sotuv guruhidagi
    # oddiy yozishmalarga javob bermaydi.
    if chat.get("type") != "private":
        if cmd in ("/stat", "/royxat") and _is_admin(user.get("id"), chat_id):
            (_stat if cmd == "/stat" else _royxat)(db, chat_id)
        return

    s, d = _get_session(db, chat_id)
    if cmd == "/start":
        _start(db, s, chat_id)
        return
    if cmd == "/cancel":
        _cancel(db, s, chat_id)
        return
    if cmd in ("/stat", "/royxat"):
        if _is_admin(user.get("id"), chat_id):
            (_stat if cmd == "/stat" else _royxat)(db, chat_id)
        else:
            _send(chat_id, "❌ Bu buyruq faqat adminlar uchun.",
                  parse_mode=None)
        return
    if cmd == "/broadcast":
        if not _admin_ids():
            _send(chat_id, "⚠️ Broadcast ishlashi uchun ACADEMY_ADMIN_IDS "
                           "sozlanmagan.", parse_mode=None)
        elif str(user.get("id")) not in _admin_ids():
            _send(chat_id, "❌ Bu buyruq faqat adminlar uchun.",
                  parse_mode=None)
        else:
            _send(chat_id,
                  "📢 <b>Broadcast rejimi</b>\n\nBarcha ro'yxatdan o'tgan "
                  "foydalanuvchilarga yuboriladigan xabarni yozing.\n\n"
                  "Bekor qilish: /cancel")
            _save(db, s, "broadcast", {})
        return
    if cmd:
        return  # noma'lum buyruq — jim

    st = s.state
    if st == "broadcast":
        if str(user.get("id")) in _admin_ids() and text:
            _broadcast_send(db, s, chat_id, text)
        return
    if st == "name" and text:
        _ask_phone(db, s, d, chat_id, text)
    elif st == "phone":
        _ask_grade(db, s, d, chat_id, msg)
    elif st == "grade" and text:
        _ask_course(db, s, d, chat_id, text)
    elif st == "confirm":
        if text == YES:
            _confirm(db, s, d, chat_id, user)
        elif text == NO:
            _cancel(db, s, chat_id)
    elif st is None and text:
        # Suhbat boshlanmagan — eski botda javob yo'q edi; endi yo'l
        # ko'rsatamiz.
        _send(chat_id, "Ro'yxatdan o'tish uchun /start bosing.",
              parse_mode=None)


# ─── Marshrutlar ─────────────────────────────────────────────────────────

@router.post("/api/tg/academy-bot/{secret}")
async def academy_webhook(secret: str, request: Request,
                          db: Session = Depends(get_db)):
    """Telegram webhook. Sir manzilda ham, sarlavhada ham tekshiriladi.
    Har doim 200 qaytaramiz — aks holda Telegram bitta xatoli xabarni
    qayta-qayta yuborib, keyingilarini to'sib qo'yadi."""
    if not enabled() or secret != webhook_secret():
        raise HTTPException(404, "Not found")
    hdr = request.headers.get("x-telegram-bot-api-secret-token", "")
    if hdr != webhook_secret():
        raise HTTPException(404, "Not found")
    try:
        upd = await request.json()
    except Exception:
        return {"ok": True}
    try:
        handle_update(db, upd)
    except Exception:
        db.rollback()
    return {"ok": True}


@router.post("/api/tg/academy-bot-setup")
def academy_setup(request: Request,
                  user=Depends(require_role(roles.FOUNDER))):
    """Botni webhookka ulash (asoschi, bir marta). Token Vercel'da —
    bu yerda faqat Telegram'ga "xabarlarni shu manzilga yubor" deyiladi."""
    if not enabled():
        raise HTTPException(400, "ACADEMY_BOT_TOKEN Vercel'da o'rnatilmagan")
    base = os.environ.get("PUBLIC_BASE_URL", "https://jonyos.uz").rstrip("/")
    url = f"{base}/api/tg/academy-bot/{webhook_secret()}"
    r = tg("setWebhook", {"url": url, "secret_token": webhook_secret(),
                          "allowed_updates": ["message", "callback_query"],
                          "drop_pending_updates": False})
    me = tg("getMe", {}) or {}
    tg("setMyCommands", {"commands": [
        {"command": "start", "description": "Ro'yxatdan o'tish"},
        {"command": "cancel", "description": "Bekor qilish"}]})
    return {"ok": bool(r and r.get("ok")),
            "telegram": (r or {}).get("description"),
            "bot": ((me.get("result") or {}).get("username")),
            "sales_group": bool(_sales_group()),
            "admins": len(_admin_ids())}


@router.get("/api/tg/academy-bot-status")
def academy_status(user=Depends(require_role(roles.FOUNDER))):
    if not enabled():
        return {"enabled": False}
    info = tg("getWebhookInfo", {}) or {}
    res = info.get("result") or {}
    return {"enabled": True,
            "webhook_ok": (res.get("url") or "").endswith(webhook_secret()),
            "pending": res.get("pending_update_count"),
            "last_error": res.get("last_error_message"),
            "sales_group": bool(_sales_group()),
            "admins": len(_admin_ids())}
