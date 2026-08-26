# -*- coding: utf-8 -*-
"""Imtihonlar ikki qavatli bo'lishi kerak: IELTS | CEFR | SAT.

Jahongir: "Yoq yanada alohida qil, IELTS va CEFR alohida tursin
SAT ham alohida tursin, keyin IELTSga kirganda Reading listening
writing speaking, tursin CEFR ga kirganda ham shunaqa."

Bu test uch narsani qo'riqlaydi:
  1. Ro'yxat (examsConfig.ts) va marshrut (App.tsx) mos turishi.
  2. Bosh ekranda yana ko'nikmalar ARALASHIB ketmasligi.
  3. Har bir havola tirik ekani — "?exam=X" filtri serverda
     haqiqatan mashq qaytarishi. O'lik tugma qolmasin.
"""
import re
import os

SRC = os.path.join(os.path.dirname(__file__), "..", "src", "pages", "student")


def _read(name):
    with open(os.path.join(SRC, name), encoding="utf-8") as f:
        return f.read()


def _exam_bloklar():
    """examsConfig.ts dan { key: "...", ... } bloklarini ajratadi."""
    s = _read("examsConfig.ts")
    s = s[s.index("export const EXAMS"):]
    parts = re.split(r'\n    key: "', s)[1:]
    out = []
    for p in parts:
        key = p[: p.index('"')]
        out.append((key, p))
    return out


# ---------- 1. Tuzilma ----------

def test_uchta_imtihon():
    keys = [k for k, _ in _exam_bloklar()]
    assert keys == ["ielts", "cefr", "sat"], keys


def test_ielts_va_cefrda_tortta_konikma():
    """Jahongir: "Reading listening writing speaking"."""
    for key, blok in _exam_bloklar():
        if key == "sat":
            continue
        kutilgan = {"listening", "reading", "writing", "speaking"}
        bor = set(re.findall(r'\n        key: "([a-z]+)"', blok))
        assert bor == kutilgan, (key, bor)


def test_sat_alohida_tuzilmada():
    """SAT'da listening/speaking YO'Q — yo'q narsa ko'rsatilmaydi."""
    blok = dict(_exam_bloklar())["sat"]
    bor = set(re.findall(r'\n        key: "([a-z]+)"', blok))
    assert bor == {"rw", "math"}, bor
    assert "ready: false" in blok
    assert "href:" not in blok, "SAT'da hali ishlaydigan havola yo'q"


# ---------- 2. Ekranlar ----------

def test_bosh_ekranda_konikma_yoq():
    """Bosh ekran faqat imtihonlarni ko'rsatadi, mashqni emas."""
    s = _read("StudentIelts.tsx")
    assert "/student/ielts/exam/${e.key}" in s
    for yomon in ("/student/ielts/listening", "/student/ielts/reading"):
        assert yomon not in s, yomon


def test_marshrut_bor():
    with open(os.path.join(SRC, "..", "..", "App.tsx"), encoding="utf-8") as f:
        s = f.read()
    assert 'path="ielts/exam/:exam"' in s
    assert "StudentExamSkills" in s


def test_ichki_ekran_royxatdan_oladi():
    """Ko'nikmalar qo'lda emas, examsConfig'dan kelishi kerak."""
    s = _read("StudentExamSkills.tsx")
    assert "findExam" in s
    assert "useParams" in s


# ---------- 3. Havolalar tirikmi ----------

def _hrefs():
    out = []
    for key, blok in _exam_bloklar():
        for h in re.findall(r'href: "([^"]+)"', blok):
            out.append((key, h))
    return out


def test_havolalar_exam_tegiga_mos():
    """?exam= li havola O'Z imtihoniga ishora qilishi kerak.

    2026-08-26: CEFR Writing o'z bo'limiga ega bo'ldi
    (/student/cefr/writing) — unda ?exam= yo'q, chunki u
    umumiy reading/listening ro'yxatidan foydalanmaydi.
    """
    for key, h in _hrefs():
        if "?exam=" in h:
            assert h.endswith("?exam=" + key), (key, h)
        else:
            assert h.startswith("/student/"), h


def test_har_havola_mashq_qaytaradi():
    """Server shu filtr bilan bo'sh ro'yxat qaytarsa — o'lik tugma."""
    import student_app as sa
    for key, h in _hrefs():
        m = re.match(r"/student/ielts/(listening|reading)\?exam=", h)
        if not m:
            continue
        rows = (sa.IELTS_PARTS if m.group(1) == "listening"
                else sa.READING_TYPES)
        qism = sa._exam_parts(rows, key)
        assert len(qism) >= 2, (h, len(qism))


def test_cefr_writing_havolasi_tirik():
    """CEFR Writing kartasi bosilganda bo'sh ekran chiqmasin."""
    import cefr_writing_guide as g
    import cefr_writing_drills as d
    import cefr_writing_tasks as t
    cfg = _read("examsConfig.ts")
    assert "/student/cefr/writing" in cfg
    with open(os.path.join(SRC, "..", "..", "App.tsx"),
              encoding="utf-8") as f:
        app = f.read()
    assert 'path="cefr/writing"' in app
    assert len(g.GUIDE) >= 10
    assert sum(d.counts().values()) >= 150
    assert len(t.PART1) + len(t.PART2) >= 25


def test_ikkala_imtihonda_ham_qism_bor():
    import student_app as sa
    for exam in ("ielts", "cefr"):
        assert len(sa._exam_parts(sa.IELTS_PARTS, exam)) >= 5
        assert len(sa._exam_parts(sa.READING_TYPES, exam)) >= 5
