"""LUG'AT PDF (2026-09-18, Jahongir: "Lugat bolimida 20/40/60 qilgansan
har birni yuklab olish imkoniyati bo'lishi kerak, pdf shaklda").

GET /api/plans/{course}/{no}/vocab.pdf?tier=20|40|60 — dars lug'ati
albom (landscape) jadval: №, so'z, o'qilishi, tarjima, misol gap,
tarjimasi. Brendlangan: logo + JONY ACADEMY sarlavha, kontakt, pastda
reklama qatori, och suv belgisi. Shrift — DejaVu Sans (IPA belgilari
uchun; api/assets/fonts).
"""
import io
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session

import roles
from auth import require_role
from database import get_db
from liveplay import _lesson, _english_only

router = APIRouter()

_ASSETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
BRAND = "JONY ACADEMY"
CONTACT = "+998 77 276 97 77 · +998 93 112 65 65 · jonyacademy.uz · @JonyAcademybot"
AD = ("Jony Academy — ingliz tili, IELTS va Jony Student ilovasi bilan "
      "o'yin orqali o'rganish. Ro'yxatdan o'tish: jonyacademy.uz")
TIERS = {"20": ("core",), "40": ("core", "strong"), "60": ("core", "strong", "super")}
TIER_LABEL = {"20": "CORE 20", "40": "CORE + STRONG (40)", "60": "CORE + STRONG + SUPER (60)"}

_fonts_ready = False


def _fonts():
    global _fonts_ready
    if _fonts_ready:
        return
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    pdfmetrics.registerFont(TTFont("DV", os.path.join(_ASSETS, "fonts", "DejaVuSans.ttf")))
    pdfmetrics.registerFont(TTFont("DV-B", os.path.join(_ASSETS, "fonts", "DejaVuSans-Bold.ttf")))
    _fonts_ready = True


def build_vocab_pdf(L: dict, tier: str) -> bytes:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    _fonts()
    V = L.get("vocab") or {}
    keys = TIERS.get(tier) or TIERS["20"]
    blue = colors.HexColor("#1A6FE4")
    grey = colors.HexColor("#7F7F7F")
    st_cell = ParagraphStyle("c", fontName="DV", fontSize=8.2, leading=10)
    st_word = ParagraphStyle("w", fontName="DV-B", fontSize=8.6, leading=10.5)
    st_ipa = ParagraphStyle("i", fontName="DV", fontSize=8, leading=10, textColor=colors.HexColor("#444444"))
    st_h = ParagraphStyle("h", fontName="DV-B", fontSize=13, leading=16, textColor=colors.HexColor("#0F172A"))
    st_sub = ParagraphStyle("s", fontName="DV", fontSize=8.5, leading=11, textColor=grey)
    st_tier = ParagraphStyle("t", fontName="DV-B", fontSize=10.5, leading=13, textColor=blue, spaceBefore=6)
    tier_titles = {"core": "CORE 20 — hamma uchun (majburiy)",
                   "strong": "STRONG — kuchli o'quvchi uchun (+20, jami 40)",
                   "super": "SUPER — eng kuchli o'quvchi uchun (+20, jami 60)"}

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=landscape(A4), leftMargin=1.2 * cm, rightMargin=1.2 * cm,
                            topMargin=1.9 * cm, bottomMargin=1.6 * cm,
                            title=f"Dars {L['no']} — lug'at ({TIER_LABEL.get(tier, tier)})",
                            author=BRAND)
    W = landscape(A4)[0] - 2.4 * cm
    story = [Paragraph(f"Dars {L['no']} — {L['title']}", st_h),
             Paragraph(f"Lug'at: {L.get('vocab_topic', '')} · Grammatika: {L.get('grammar_topic', '')} · "
                       f"{TIER_LABEL.get(tier, tier)}", st_sub), Spacer(1, 4)]
    n = 0
    for k in keys:
        rows = V.get(k) or []
        if not rows:
            continue
        story.append(Paragraph(tier_titles[k], st_tier))
        data = [["№", "So'z", "O'qilishi", "Tarjimasi", "Misol gap", "Gap tarjimasi"]]
        for e in rows:
            n += 1
            w, uz = e[0], e[1]
            ex, ex_uz = (e[2] if len(e) > 2 else ""), (e[3] if len(e) > 3 else "")
            ipa = e[4] if len(e) > 4 and e[4] else ""
            data.append([str(n), Paragraph(w, st_word), Paragraph(f"/{ipa}/" if ipa else "", st_ipa),
                         Paragraph(uz, st_cell), Paragraph(ex, st_cell), Paragraph(ex_uz, st_cell)])
        t = Table(data, colWidths=[0.9 * cm, W * 0.17, W * 0.15, W * 0.17, W * 0.26, W * 0.22],
                  repeatRows=1)
        t.setStyle(TableStyle([
            ("FONTNAME", (0, 0), (-1, 0), "DV-B"), ("FONTSIZE", (0, 0), (-1, 0), 8.5),
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#D9E2F3")),
            ("FONTNAME", (0, 1), (0, -1), "DV"), ("FONTSIZE", (0, 1), (0, -1), 8),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#B0B8C4")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F5F8FD")]),
            ("TOPPADDING", (0, 0), (-1, -1), 2.5), ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
        ]))
        story.append(t)
    if n == 0:
        raise HTTPException(404, "Bu darsda lug'at yo'q")

    logo = os.path.join(_ASSETS, "brand-icon.png")

    def deco(canvas, d):
        canvas.saveState()
        pw, ph = landscape(A4)
        # suv belgisi — och, diagonal, o'qishga xalaqit bermaydi
        canvas.setFont("DV-B", 58)
        canvas.setFillColor(colors.Color(0.72, 0.8, 0.92, alpha=0.16))
        canvas.translate(pw / 2, ph / 2)
        canvas.rotate(28)
        canvas.drawCentredString(0, 0, BRAND)
        canvas.restoreState()
        canvas.saveState()
        # sarlavha
        y = ph - 1.25 * cm
        if os.path.exists(logo):
            canvas.drawImage(logo, 1.2 * cm, y - 0.15 * cm, width=0.62 * cm, height=0.62 * cm,
                             mask="auto")
        canvas.setFont("DV-B", 10.5)
        canvas.setFillColor(blue)
        canvas.drawString(2.0 * cm, y, BRAND)
        canvas.setFont("DV", 7.5)
        canvas.setFillColor(grey)
        canvas.drawRightString(pw - 1.2 * cm, y, CONTACT)
        canvas.setStrokeColor(colors.HexColor("#D9E2F3"))
        canvas.line(1.2 * cm, y - 0.35 * cm, pw - 1.2 * cm, y - 0.35 * cm)
        # pastki qator
        canvas.setFont("DV", 7.2)
        canvas.setFillColor(blue)
        canvas.drawCentredString(pw / 2, 0.95 * cm, AD)
        canvas.setFillColor(grey)
        canvas.drawCentredString(pw / 2, 0.55 * cm, f"© Jony Academy · {CONTACT} · sahifa {d.page}")
        canvas.restoreState()

    doc.build(story, onFirstPage=deco, onLaterPages=deco)
    return buf.getvalue()


@router.get("/api/plans/{course}/{no}/vocab.pdf")
def vocab_pdf(course: str, no: int, tier: str = "20", db: Session = Depends(get_db),
              user=Depends(require_role(*roles.PLANS_ACCESS))):
    _english_only(db, user)
    L = _lesson(course, no)
    tier = tier if tier in TIERS else "20"
    pdf = build_vocab_pdf(L, tier)
    fname = f"Dars {L['no']} - lugat {tier}.pdf"
    return Response(pdf, media_type="application/pdf",
                    headers={"Content-Disposition": f'attachment; filename="{fname}"'})
