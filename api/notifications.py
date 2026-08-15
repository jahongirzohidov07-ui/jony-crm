"""Auto-extracted from main.py during refactor (split-main). Domain: notifications."""
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

# notifications.py ichida marketing domenidagi funksiya to'g'ridan-to'g'ri
# chaqiriladi - bo'linishdan oldin bitta fayl bo'lgani uchun ishlagan,
# endi aniq import kerak.
from marketing import marketing_rfm

router = APIRouter()

def _ensure_templates(db: Session) -> None:
    have = {t.kind for t in db.query(models.NotifyTemplate).all()}
    for kind, (title, body) in roles.DEFAULT_TEMPLATES.items():
        if kind in have:
            continue
        db.add(models.NotifyTemplate(
            kind=kind, title=title, body=body,
            days_before=roles.NOTIFY_DEFAULT_DAYS.get(kind, 0)))
    db.commit()

def _fill(body: str, **kw) -> str:
    out = body
    for k, v in kw.items():
        out = out.replace("{" + k + "}", str(v if v is not None else ""))
    return out

def _money(v) -> str:
    return f"{round(v or 0):,}".replace(",", " ")

@router.get("/api/notifications/templates")
def notify_templates(
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.NOTIFY_ACCESS)),
):
    _ensure_templates(db)
    rows = db.query(models.NotifyTemplate).all()
    order = [k for k, _, _ in roles.NOTIFY_KINDS]
    rows.sort(key=lambda t: order.index(t.kind) if t.kind in order else 99)
    return {
        "rows": [{
            "id": t.id, "kind": t.kind,
            "kind_label": roles.NOTIFY_KIND_LABELS.get(t.kind, t.kind),
            "title": t.title, "body": t.body,
            "channel": t.channel, "active": bool(t.active),
            "days_before": t.days_before or 0,
        } for t in rows],
        "channels": [{"key": k, "label": lbl}
                     for k, lbl in roles.NOTIFY_CHANNELS],
        "placeholders": ["{ism}", "{summa}", "{sana}", "{guruh}", "{kurs}"],
        "telegram_ready": bool(os.environ.get("TELEGRAM_BOT_TOKEN")),
    }

@router.put("/api/notifications/templates/{tid}")
def update_notify_template(
    tid: int,
    payload: schemas.TemplateUpdate,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.NOTIFY_ACCESS)),
):
    t = db.query(models.NotifyTemplate).get(tid)
    if not t:
        raise HTTPException(404, "Shablon topilmadi")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(t, k, 1 if k == "active" and v else (0 if k == "active" else v))
    db.commit()
    return {"ok": True}


@router.post("/api/notifications/generate")
def generate_notifications(
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.NOTIFY_ACCESS)),
):
    """AVTOMAT: bugungi tug'ilgan kunlar, to'lov eslatmalari va
    qarzdorlik xabarlarini navbatga qo'yadi. Takror yaratilmaydi."""
    _ensure_templates(db)
    today = date.today()
    tpl = {t.kind: t for t in db.query(models.NotifyTemplate).all()
           if t.active}

    students = scope_to_branch(db.query(models.Student), models.Student,
                               user).filter(
        models.Student.status.in_(["active", "trial"])).all()

    made = {k: 0 for k in roles.NOTIFY_KIND_LABELS}

    def already(kind, sid, on):
        return (db.query(models.Notification)
                .filter(models.Notification.kind == kind,
                        models.Notification.student_id == sid,
                        models.Notification.scheduled_for == on).first())

    for s in students:
        phone = s.phone or s.parent_phone

        # --- Tug'ilgan kun ---
        t = tpl.get("birthday")
        if t and s.birth_date and (s.birth_date.month, s.birth_date.day) == \
                (today.month, today.day) and not already("birthday", s.id, today):
            db.add(models.Notification(
                kind="birthday", channel=t.channel, student_id=s.id,
                phone=phone, title=t.title,
                body=_fill(t.body, ism=s.full_name),
                scheduled_for=today, created_by="Tizim"))
            made["birthday"] += 1

        bal = student_balance(db, s.id)

        # --- Qarzdorlik ---
        t = tpl.get("debt")
        if t and bal < 0 and not already("debt", s.id, today):
            db.add(models.Notification(
                kind="debt", channel=t.channel, student_id=s.id,
                phone=phone, title=t.title,
                body=_fill(t.body, ism=s.full_name, summa=_money(abs(bal))),
                scheduled_for=today, created_by="Tizim"))
            made["debt"] += 1

        # --- To'lov eslatmasi: oy oxiriga N kun qolganda ---
        t = tpl.get("payment_due")
        if t and bal >= 0:
            _s0, m_end = billing.month_bounds(today.year, today.month)
            days_left = (m_end - today).days
            if days_left == (t.days_before or 3) and s.group:
                if not already("payment_due", s.id, today):
                    db.add(models.Notification(
                        kind="payment_due", channel=t.channel,
                        student_id=s.id, phone=phone, title=t.title,
                        body=_fill(t.body, ism=s.full_name,
                                   sana=m_end.isoformat(),
                                   summa=_money(s.group.monthly_fee)),
                        scheduled_for=today, created_by="Tizim"))
                    made["payment_due"] += 1

    db.commit()
    total = sum(made.values())
    return {
        "created": total,
        "by_kind": [{"key": k, "label": roles.NOTIFY_KIND_LABELS[k],
                     "count": v} for k, v in made.items() if v],
        "date": today.isoformat(),
    }

@router.get("/api/notifications")
def list_notifications(
    status_filter: str | None = None,
    kind: str | None = None,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.NOTIFY_ACCESS)),
):
    q = db.query(models.Notification)
    if status_filter:
        q = q.filter(models.Notification.status == status_filter)
    if kind:
        q = q.filter(models.Notification.kind == kind)
    rows = q.order_by(models.Notification.created_at.desc()).limit(300).all()

    counts = {}
    for n in db.query(models.Notification).all():
        counts[n.status] = counts.get(n.status, 0) + 1

    return {
        "rows": [{
            "id": n.id,
            "kind": n.kind,
            "kind_label": roles.NOTIFY_KIND_LABELS.get(n.kind, n.kind),
            "channel": n.channel,
            "channel_label": roles.NOTIFY_CHANNEL_LABELS.get(n.channel, n.channel),
            "student_id": n.student_id,
            "student": n.student.full_name if n.student else None,
            "phone": n.phone,
            "title": n.title,
            "body": n.body,
            "status": n.status,
            "status_label": roles.NOTIFY_STATUS_LABELS.get(n.status, n.status),
            "tone": roles.NOTIFY_STATUS_TONE.get(n.status, "slate"),
            "scheduled_for": (n.scheduled_for.isoformat()
                              if n.scheduled_for else None),
            "sent_at": n.sent_at.isoformat() if n.sent_at else None,
            "error": n.error,
        } for n in rows],
        "counts": counts,
        "statuses": [{"key": k, "label": lbl, "tone": t,
                      "count": counts.get(k, 0)}
                     for k, lbl, t in roles.NOTIFY_STATUSES],
        "kinds": [{"key": k, "label": lbl}
                  for k, lbl, _ in roles.NOTIFY_KINDS],
        "telegram_ready": bool(os.environ.get("TELEGRAM_BOT_TOKEN")),
    }

@router.post("/api/notifications/{nid}/status")
def set_notification_status(
    nid: int,
    payload: schemas.NotifyStatus,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.NOTIFY_ACCESS)),
):
    n = db.query(models.Notification).get(nid)
    if not n:
        raise HTTPException(404, "Topilmadi")
    if payload.status not in roles.NOTIFY_STATUS_LABELS:
        raise HTTPException(400, "Noto'g'ri holat")
    n.status = payload.status
    if payload.status == "sent":
        n.sent_at = datetime.utcnow()
    db.commit()
    return {"ok": True}

@router.post("/api/notifications/custom")
def custom_notification(
    payload: schemas.NotifyCreate,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.NOTIFY_ACCESS)),
):
    """Qo'lda xabar: yangi kurs, taklif va h.k. Segment bo'yicha
    bir vaqtda yuborish mumkin."""
    if not payload.body.strip():
        raise HTTPException(400, "Xabar matnini yozing")

    targets = []
    if payload.student_ids:
        targets = (db.query(models.Student)
                   .filter(models.Student.id.in_(payload.student_ids)).all())
    elif payload.segment:
        rfm = marketing_rfm(branch_id=None, db=db, user=user)
        ids = [r["student_id"] for r in rfm["rows"]
               if r["segment"] == payload.segment]
        targets = (db.query(models.Student)
                   .filter(models.Student.id.in_(ids or [-1])).all())
    if not targets:
        raise HTTPException(400, "Kimga yuborishni tanlang")

    for s in targets:
        db.add(models.Notification(
            kind=payload.kind or "new_course",
            channel=payload.channel,
            student_id=s.id, phone=s.phone or s.parent_phone,
            title=payload.title,
            body=_fill(payload.body, ism=s.full_name,
                       guruh=s.group.name if s.group else "",
                       kurs=payload.course or ""),
            scheduled_for=date.today(), created_by=user.full_name))
    db.commit()
    return {"created": len(targets)}

def _seed_replies(db: Session) -> None:
    have = {r.key for r in db.query(models.InboxReply).all()}
    added = False
    for key, label, text in roles.QUICK_REPLIES:
        if key in have:
            continue
        db.add(models.InboxReply(key=key, label=label, text=text,
                                 is_active=1))
        added = True
    if added:
        db.commit()

def _is_off_hours(when: datetime) -> bool:
    """Xabar ish vaqtidan tashqari keldimi.

    MUHIM: server UTC'da, markaz esa Toshkent vaqtida ishlaydi. Shu
    farq hisobga olinmasa, soat 21:00 da kelgan xabar "ish vaqtida
    keldi" deb sanaladi va xodim yo'q aybi uchun javob beradi."""
    start = roles.time_to_minutes(roles.INBOX_WORK_START) or 0
    end = roles.time_to_minutes(roles.INBOX_WORK_END) or 1440
    local = roles.to_local(when)
    mins = local.hour * 60 + local.minute
    return mins < start or mins > end

def _msg_out(db: Session, m: models.SocialMessage,
             users: dict | None = None) -> dict:
    users = users if users is not None else {
        u.id: u.full_name for u in db.query(models.User).all()}
    waiting = None
    if not m.first_reply_at and m.received_at:
        waiting = round(
            (datetime.utcnow() - m.received_at).total_seconds() / 60, 1)
    band, band_label, tone = roles.sla_band(
        m.reply_minutes if m.first_reply_at else None)
    return {
        "id": m.id,
        "channel": m.channel,
        "channel_label": roles.CHANNEL_LABELS.get(m.channel, m.channel),
        "channel_tone": roles.CHANNEL_TONE.get(m.channel, "slate"),
        "kind": m.kind,
        "kind_label": roles.MESSAGE_KIND_LABELS.get(m.kind, m.kind),
        "author": m.author or m.username or "—",
        "username": m.username,
        "phone": m.phone,
        "text": m.text,
        "content_id": m.content_id,
        "content": m.content.title if m.content else None,
        "content_code": m.content.content_id if m.content else None,
        "course": m.course,
        "status": m.status,
        "status_label": roles.INBOX_STATUS_LABELS.get(m.status, m.status),
        "status_tone": roles.INBOX_STATUS_TONE.get(m.status, "slate"),
        "assigned": users.get(m.assigned_to),
        "lead_id": m.lead_id,
        "received_at": m.received_at.isoformat() if m.received_at else None,
        "first_reply_at": (m.first_reply_at.isoformat()
                           if m.first_reply_at else None),
        "reply_minutes": m.reply_minutes,
        "waiting_minutes": waiting,
        "off_hours": bool(m.off_hours),
        "sla": band, "sla_label": band_label, "sla_tone": tone,
        "overdue": bool(waiting and waiting > roles.SLA_ALERT_MINUTES),
        "reply_text": m.reply_text,
        "replied_by": m.replied_by,
    }

@router.get("/api/inbox")
def list_inbox(
    status: str | None = None,
    channel: str | None = None,
    content_id: int | None = None,
    only_open: bool = False,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.INBOX_ACCESS)),
):
    """Barcha murojaatlar bitta oynada."""
    _seed_replies(db)
    q = db.query(models.SocialMessage)
    if status:
        q = q.filter(models.SocialMessage.status == status)
    if only_open:
        q = q.filter(models.SocialMessage.status.in_(roles.INBOX_OPEN))
    if channel:
        q = q.filter(models.SocialMessage.channel == channel)
    if content_id:
        q = q.filter(models.SocialMessage.content_id == content_id)
    rows = (q.order_by(models.SocialMessage.received_at.desc())
            .limit(300).all())
    users = {u.id: u.full_name for u in db.query(models.User).all()}
    out = [_msg_out(db, m, users) for m in rows]

    everything = db.query(models.SocialMessage).all()
    counts: dict = {}
    for m in everything:
        counts[m.status] = counts.get(m.status, 0) + 1

    # SLA: faqat ish vaqtida kelganlar bo'yicha
    answered = [m for m in everything if m.first_reply_at and not m.off_hours]
    in_time = [m for m in answered
               if (m.reply_minutes or 0) <= roles.SLA_ALERT_MINUTES]
    sla_pct = round(len(in_time) / len(answered) * 100, 1) if answered else 0.0
    avg = (round(sum(m.reply_minutes or 0 for m in answered) / len(answered), 1)
           if answered else 0.0)

    return {
        "rows": out,
        "counts": counts,
        "open": len([m for m in everything if m.status in roles.INBOX_OPEN]),
        "overdue": len([r for r in out if r["overdue"]]),
        "sla_percent": sla_pct,
        "avg_minutes": avg,
        "answered": len(answered),
        "off_hours": len([m for m in everything if m.off_hours]),
        "statuses": [{"key": k, "label": lbl, "tone": t,
                      "count": counts.get(k, 0)}
                     for k, lbl, t in roles.INBOX_STATUSES],
        "channels": [{"key": k, "label": lbl, "tone": t}
                     for k, lbl, t in roles.INBOX_CHANNELS],
        "sla_alert": roles.SLA_ALERT_MINUTES,
        "work_hours": f"{roles.INBOX_WORK_START}–{roles.INBOX_WORK_END}",
        "templates": [{"id": r.id, "key": r.key, "label": r.label,
                       "text": r.text}
                      for r in db.query(models.InboxReply)
                      .filter(models.InboxReply.is_active == 1).all()],
        "hint": ("Ish vaqtidan tashqari kelgan murojaatlar SLA hisobiga "
                 "kirmaydi — tunda kelgan xabar uchun aybdor bo'lmaysiz."),
    }

@router.post("/api/inbox")
def add_message(
    payload: schemas.MessageCreate,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.INBOX_ACCESS)),
):
    """Murojaatni qo'lda kiritish. Integratsiya ulanganda tizim
    o'zi tortadi."""
    if payload.external_id:
        dup = (db.query(models.SocialMessage)
               .filter(models.SocialMessage.external_id
                       == payload.external_id).first())
        if dup:
            return _msg_out(db, dup)
    when = payload.received_at or datetime.utcnow()
    m = models.SocialMessage(
        **payload.model_dump(exclude={"received_at"}),
        received_at=when, status="new",
        off_hours=1 if _is_off_hours(when) else 0)
    db.add(m)
    db.commit()
    return _msg_out(db, m)

@router.post("/api/inbox/{mid}/reply")
def reply_message(
    mid: int,
    payload: schemas.MessageReply,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.INBOX_ACCESS)),
):
    """Javob berildi deb belgilash. Birinchi javob vaqti bir marta
    yoziladi — keyingi javoblar SLA'ni o'zgartirmaydi."""
    m = db.query(models.SocialMessage).get(mid)
    if not m:
        raise HTTPException(404, "Murojaat topilmadi")
    now = datetime.utcnow()
    if not m.first_reply_at:
        m.first_reply_at = now
        if m.received_at:
            m.reply_minutes = round(
                (now - m.received_at).total_seconds() / 60, 1)
    m.reply_text = payload.text
    m.replied_by = user.full_name
    m.status = payload.status or "answered"
    db.commit()
    return _msg_out(db, m)

@router.post("/api/inbox/{mid}/status")
def set_message_status(
    mid: int,
    payload: schemas.MessageStatus,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.INBOX_ACCESS)),
):
    m = db.query(models.SocialMessage).get(mid)
    if not m:
        raise HTTPException(404, "Murojaat topilmadi")
    if payload.status not in roles.INBOX_STATUS_LABELS:
        raise HTTPException(400, "Bunday holat yo'q")
    m.status = payload.status
    if payload.note:
        m.note = payload.note
    db.commit()
    return _msg_out(db, m)

@router.post("/api/inbox/{mid}/lead")
def message_to_lead(
    mid: int,
    payload: schemas.MessageToLead,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.INBOX_ACCESS)),
):
    """Murojaatni bir tugma bilan leadga aylantiradi. Kontent va
    kampaniya ham ko'chadi — shundan keyin "qaysi kontent sotuv olib
    keldi" savoliga javob bo'ladi."""
    m = db.query(models.SocialMessage).get(mid)
    if not m:
        raise HTTPException(404, "Murojaat topilmadi")
    if m.lead_id:
        raise HTTPException(400, "Bu murojaat allaqachon leadga "
                                 "aylantirilgan")

    name = (payload.full_name or m.author or m.username or "").strip()
    if not name:
        raise HTTPException(400, "Ism yozing")

    lead = models.Lead(
        full_name=name,
        phone=payload.phone or m.phone,
        source="instagram" if m.channel == "instagram" else "telegram"
        if m.channel == "telegram" else "other",
        stage="new",
        note=(payload.note or m.text),
        branch_id=payload.branch_id or m.branch_id,
        assigned_user_id=payload.assigned_user_id,
        content_id=m.content_id,
        campaign_id=m.campaign_id,
        social_message_id=m.id,
    )
    db.add(lead)
    db.commit()
    db.refresh(lead)
    _ensure_public_id(db, "lead", lead)
    m.lead_id = lead.id
    m.status = "lead"
    db.commit()
    return {"ok": True, "lead_id": lead.id,
            "public_id": lead.public_id,
            "message": "Lead yaratildi va sotuv bo'limiga tushdi"}

@router.put("/api/inbox/templates/{tid}")
def update_template(
    tid: int,
    payload: schemas.ReplyTemplate,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.SMM_ACCESS)),
):
    t = db.query(models.InboxReply).get(tid)
    if not t:
        raise HTTPException(404, "Shablon topilmadi")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(t, k, 1 if k == "is_active" and v else
                (0 if k == "is_active" else v))
    db.commit()
    return {"ok": True}

@router.get("/api/telegram/status")
def telegram_status(db: Session = Depends(get_db),
                    user=Depends(require_role(roles.FOUNDER))):
    """Bot sozlanganmi, @username nima, webhook ulash tugmasi uchun."""
    if not notify.enabled():
        return {"enabled": False,
                "hint": "Vercel'da TELEGRAM_BOT_TOKEN o'rnatilmagan"}
    linked = db.query(models.Student).filter(
        models.Student.telegram_chat_id.isnot(None)).count()
    return {"enabled": True, "bot": notify.bot_info(), "linked": linked}

@router.post("/api/telegram/setup-webhook")
def telegram_setup(request: Request,
                   user=Depends(require_role(roles.FOUNDER))):
    """Botga webhook manzilini o'rnatadi — bir marta bosiladi."""
    if not notify.enabled():
        raise HTTPException(400, "TELEGRAM_BOT_TOKEN o'rnatilmagan")
    base = os.environ.get("PUBLIC_URL", "https://jony-crm.vercel.app")
    ok = notify.set_webhook(
        f"{base}/api/telegram/webhook?secret={notify.webhook_secret()}")
    if not ok:
        raise HTTPException(502, "Telegram webhook o'rnatilmadi")
    return {"ok": True}

@router.post("/api/telegram/webhook")
async def telegram_webhook(request: Request, secret: str = "",
                           db: Session = Depends(get_db)):
    """Telegram'dan keladigan xabarlar. Faqat /start KOD ni tushunadi."""
    if not notify.enabled() or secret != notify.webhook_secret():
        raise HTTPException(403, "Ruxsat yo'q")
    try:
        upd = await request.json()
    except Exception:
        return {"ok": True}
    msg = (upd or {}).get("message") or {}
    chat_id = str(((msg.get("chat") or {}).get("id")) or "")
    text_in = (msg.get("text") or "").strip()
    if not chat_id or not text_in:
        return {"ok": True}
    if text_in.startswith("/start"):
        code = text_in.replace("/start", "").strip().upper()
        if not code:
            notify.send(chat_id,
                        "Assalomu alaykum! Farzandingiz kartasidagi "
                        "kodni yuboring: /start KOD")
            return {"ok": True}
        s = db.query(models.Student).filter(
            models.Student.tg_code == code).first()
        if s:
            s.telegram_chat_id = chat_id
            db.commit()
            notify.send(chat_id,
                        f"Bog'landi: {s.full_name}.\nEndi davomat va "
                        "to'lov xabarlari shu yerga keladi.")
            return {"ok": True}
        # XODIM KODI (2026-08-15). Asoschiga server xatosi
        # ogohlantirishi va kunlik zaxira fayli shu chat orqali boradi.
        u = db.query(models.User).filter(
            models.User.tg_code == code,
            models.User.is_active == 1).first()
        if u:
            u.telegram_chat_id = chat_id
            db.commit()
            extra = ("\nHar kuni baza zaxirasi va server xatolari "
                     "haqida xabar shu yerga keladi."
                     if u.role == roles.FOUNDER else "")
            notify.send(chat_id,
                        f"Bog'landi: {u.full_name} "
                        f"({roles.UZ_LABELS.get(u.role, u.role)})."
                        + extra)
            return {"ok": True}
        notify.send(chat_id, "Kod topilmadi. Administratordan "
                             "qayta so'rang.")
    return {"ok": True}

