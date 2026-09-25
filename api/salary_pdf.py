"""USTOZ OYLIGI PDF (2026-09-25, Jahongir: "ustozlarni har oygi oyliki
qaysi oquvchidan qancha olishini hisobotini pdf qilib yuklab olsa
bolsin bu funksiya filial rahbarlarida ham bolsin").

GET /api/teachers/{teacher_id}/salary.pdf?year=&month=
  Filial -> guruh -> o'quvchi kesimida bitta oyning hisoboti:
  har o'quvchida keldi/kelmadi, hisobga olingan yo'qlama va summa,
  oxirida o'quvchilar bo'yicha yig'ma jadval.

Ma'lumot manbai — _salary_breakdown_scoped(), ya'ni ekrandagi
"Oylik to'liq hisoboti" bilan AYNAN bir xil raqamlar. Filialga
bog'langan rahbar faqat o'z filialini ko'radi (ustozning o'zi
ikkala filialini ham).

Brendlash lug'at PDF'idan olinadi (logo, kontakt, DejaVu shrift), lekin
pastda reklama emas — ICHKI HUJJAT ogohlantirishi turadi.
"""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session

import models
import roles
from auth import require_role
from common import _salary_breakdown_scoped, _teacher_of_user
from database import get_db
from vocab_pdf import BRAND, CONTACT, _ASSETS, _fonts

router = APIRouter()

NOTE = ("Ichki hujjat — faqat ustozning o'zi va rahbariyat uchun. "
        "Raqamlar yo'qlama asosida avtomat hisoblanadi.")


def _som(n) -> str:
    """1234000 -> "1 234 000"."""
    try:
        return f"{round(float(n or 0)):,}".replace(",", " ")
    except Exception:
        return "0"


def _safe(s: str) -> str:
    """Fayl nomi uchun — Windows ham, brauzer ham qiynalmasin."""
    out = "".join(ch for ch in str(s or "")
                  if ch.isalnum() or ch in " -_.").strip()
    return out or "hisobot"


def build_salary_pdf(d: dict) -> bytes:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.platypus import (SimpleDocTemplate, Table, TableStyle,
                                    Paragraph, Spacer, KeepTogether)
    _fonts()
    blue = colors.HexColor("#1A6FE4")
    grey = colors.HexColor("#7F7F7F")
    dark = colors.HexColor("#0F172A")
    st_h = ParagraphStyle("h", fontName="DV-B", fontSize=14, leading=17,
                          textColor=dark)
    st_sub = ParagraphStyle("s", fontName="DV", fontSize=9, leading=12,
                            textColor=grey)
    st_br = ParagraphStyle("b", fontName="DV-B", fontSize=11, leading=14,
                           textColor=blue, spaceBefore=8, spaceAfter=2)
    st_gr = ParagraphStyle("g", fontName="DV-B", fontSize=9.5, leading=12,
                           textColor=dark, spaceBefore=6, spaceAfter=2)
    st_note = ParagraphStyle("n", fontName="DV", fontSize=8, leading=10,
                             textColor=grey)
    st_cell = ParagraphStyle("c", fontName="DV", fontSize=8.5, leading=10.5)

    buf = io.BytesIO()
    title = f"{d.get('full_name')} — {d.get('title') or d.get('period')} oyligi"
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=1.4 * cm,
                            rightMargin=1.4 * cm, topMargin=2.0 * cm,
                            bottomMargin=1.7 * cm, title=title, author=BRAND)
    W = A4[0] - 2.8 * cm

    scope = ""
    if d.get("scoped") and d.get("scope_branches"):
        scope = " · " + ", ".join(d["scope_branches"]) + " bo'yicha"
    story = [
        Paragraph(f"Ustoz oyligi — {d.get('full_name')}", st_h),
        Paragraph(f"{d.get('title') or d.get('period')}{scope}", st_sub),
        Spacer(1, 6),
    ]

    # Yuqoridagi yig'ma karta
    head = [["Jami summa", "Hisobga olingan yo'qlama", "Dars kunlari",
             "Hisobga olinmagan"],
            [_som(d.get("amount")) + " so'm", str(d.get("attendances") or 0),
             str(d.get("lessons") or 0), str(d.get("not_counted") or 0)]]
    t = Table(head, colWidths=[W * 0.3, W * 0.26, W * 0.22, W * 0.22])
    t.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, 0), "DV"),
        ("FONTSIZE", (0, 0), (-1, 0), 8),
        ("TEXTCOLOR", (0, 0), (-1, 0), grey),
        ("FONTNAME", (0, 1), (-1, 1), "DV-B"),
        ("FONTSIZE", (0, 1), (-1, 1), 11),
        ("TEXTCOLOR", (0, 1), (0, 1), blue),
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F5F8FD")),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#D9E2F3")),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(t)
    if d.get("sealed"):
        story.append(Paragraph("Bu oy muhrlangan — summa qulflangan.",
                               st_note))

    hdr = ["№", "O'quvchi", "Keldi", "Kelmadi", "Hisobga olindi", "Summa"]
    widths = [0.9 * cm, W * 0.40, W * 0.10, W * 0.11, W * 0.16, W * 0.17]
    grid = TableStyle([
        ("FONTNAME", (0, 0), (-1, 0), "DV-B"), ("FONTSIZE", (0, 0), (-1, 0), 8),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#D9E2F3")),
        ("FONTNAME", (0, 1), (-1, -1), "DV"),
        ("FONTSIZE", (0, 1), (-1, -1), 8.5),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#B0B8C4")),
        ("ALIGN", (2, 0), (-1, -1), "RIGHT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1),
         [colors.white, colors.HexColor("#F7F9FC")]),
        ("TOPPADDING", (0, 0), (-1, -1), 2.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
    ])

    multi = len(d.get("branches") or []) > 1
    for br in (d.get("branches") or []):
        if multi:
            story.append(Paragraph(
                f"{br.get('branch')} — {_som(br.get('amount'))} so'm", st_br))
        for gr in (br.get("groups") or []):
            rows = [hdr]
            for i, r in enumerate(gr.get("students") or [], 1):
                nm = r.get("student") or ""
                if r.get("not_counted"):
                    nm += f"  ({r['not_counted']} ta hisobga olinmadi)"
                rows.append([str(i), Paragraph(nm, st_cell),
                             str(r.get("present") or 0),
                             str(r.get("absent") or 0),
                             str(r.get("counted") or 0),
                             _som(r.get("amount"))])
            rows.append(["", "Guruh bo'yicha jami", "", "",
                         str(gr.get("attendances") or 0),
                         _som(gr.get("amount"))])
            gt = Table(rows, colWidths=widths, repeatRows=1)
            gs = TableStyle(grid.getCommands())
            gs.add("FONTNAME", (0, -1), (-1, -1), "DV-B")
            gs.add("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#EAF1FC"))
            gt.setStyle(gs)
            cap = (f"{gr.get('group')} · {gr.get('lessons') or 0} dars · "
                   f"1 yo'qlama = {_som(gr.get('rate'))} so'm")
            story.append(KeepTogether([Paragraph(cap, st_gr), gt]))

    # O'quvchilar bo'yicha yig'ma (bir bola ikki guruhda bo'lishi mumkin)
    flat = d.get("students") or []
    if len(flat) > 1:
        story.append(Paragraph("O'quvchilar bo'yicha jami", st_br))
        rows = [["№", "O'quvchi", "Guruh(lar)", "Hisobga olindi", "Summa"]]
        for i, r in enumerate(flat, 1):
            rows.append([str(i), Paragraph(r.get("student") or "", st_cell),
                         Paragraph(r.get("groups") or "", st_cell),
                         str(r.get("counted") or 0), _som(r.get("amount"))])
        rows.append(["", "JAMI", "", str(d.get("attendances") or 0),
                     _som(d.get("amount"))])
        ft = Table(rows, colWidths=[0.9 * cm, W * 0.34, W * 0.30, W * 0.16,
                                    W * 0.17], repeatRows=1)
        fs = TableStyle(grid.getCommands())
        fs.add("FONTNAME", (0, -1), (-1, -1), "DV-B")
        fs.add("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#EAF1FC"))
        fs.add("ALIGN", (3, 0), (-1, -1), "RIGHT")
        ft.setStyle(fs)
        story.append(ft)

    story.append(Spacer(1, 6))
    story.append(Paragraph(NOTE, st_note))

    logo = os.path.join(_ASSETS, "brand-icon.png")

    def deco(canvas, doc_):
        canvas.saveState()
        pw, ph = A4
        canvas.setFont("DV-B", 54)
        canvas.setFillColor(colors.Color(0.72, 0.8, 0.92, alpha=0.13))
        canvas.translate(pw / 2, ph / 2)
        canvas.rotate(28)
        canvas.drawCentredString(0, 0, BRAND)
        canvas.restoreState()
        canvas.saveState()
        y = ph - 1.3 * cm
        if os.path.exists(logo):
            canvas.drawImage(logo, 1.4 * cm, y - 0.15 * cm, width=0.62 * cm,
                             height=0.62 * cm, mask="auto")
        canvas.setFont("DV-B", 10.5)
        canvas.setFillColor(blue)
        canvas.drawString(2.2 * cm, y, BRAND)
        canvas.setFont("DV", 7.5)
        canvas.setFillColor(grey)
        canvas.drawRightString(pw - 1.4 * cm, y, CONTACT)
        canvas.setStrokeColor(colors.HexColor("#D9E2F3"))
        canvas.line(1.4 * cm, y - 0.35 * cm, pw - 1.4 * cm, y - 0.35 * cm)
        canvas.setFont("DV", 7.2)
        canvas.setFillColor(grey)
        canvas.drawCentredString(pw / 2, 0.7 * cm,
                                 f"© Jony Academy · ichki hujjat · "
                                 f"sahifa {doc_.page}")
        canvas.restoreState()

    doc.build(story, onFirstPage=deco, onLaterPages=deco)
    return buf.getvalue()


# Boshqa ustozning oyligini ko'ra oladiganlar — teachers.py dagi
# ro'yxat bilan bir xil (filial rahbari FINANCE_ACCESS orqali kiradi,
# lekin u faqat O'Z filialini ko'radi: _salary_breakdown_scoped).
_MANAGERS = tuple(dict.fromkeys(
    tuple(roles.FINANCE_ACCESS) + tuple(roles.SALARY_VIEW_ALL)
    + (roles.ACADEMIC_HEAD, roles.HR_MANAGER)))


@router.get("/api/teachers/{teacher_id}/salary.pdf")
def teacher_salary_pdf(teacher_id: int, year: int | None = None,
                       month: int | None = None,
                       db: Session = Depends(get_db),
                       user=Depends(require_role(*roles.SALARY_SELF_VIEW))):
    """Bitta ustozning bitta oylik hisoboti — PDF."""
    t = db.query(models.Teacher).get(teacher_id)
    if not t:
        raise HTTPException(404, "Ustoz topilmadi")
    if user.role not in _MANAGERS:
        me = _teacher_of_user(db, user)
        if not me or me.id != teacher_id:
            raise HTTPException(403, "Faqat o'z oyligingizni ko'ra olasiz")
    today = roles.local_today()
    y, m = year or today.year, month or today.month
    if not 1 <= m <= 12:
        raise HTTPException(400, "Oy noto'g'ri")

    d = _salary_breakdown_scoped(db, user, t, y, m)
    if not (d.get("branches") or []):
        raise HTTPException(
            404,
            "Bu ustoz sizning filialingizda bu oyda dars bermagan"
            if d.get("scoped") else "Bu oyda yo'qlama yo'q — hisobot bo'sh")
    pdf = build_salary_pdf(d)
    fname = (f"{_safe(t.full_name)} - "
             f"{_safe(d.get('title') or d.get('period'))} oyligi.pdf")
    return Response(pdf, media_type="application/pdf",
                    headers={"Content-Disposition":
                             f'attachment; filename="{fname}"'})
