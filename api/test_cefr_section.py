# -*- coding: utf-8 -*-
"""CEFR bo'limi alohida kirish joyiga ega bo'lishi kerak.

Jahongir: "hozir men CEFR mashqarni qayerdan kiraman yoqku."

CEFR qismlari IELTS ro'yxatlari ICHIDA qolib ketgan edi: kontent
bor, lekin ekranda unga yo'l yo'q. Bu test o'sha holat qaytmasligi
uchun.
"""
import re


def _src():
    return open("student_app.py", encoding="utf-8").read()


def _blok(name):
    s = _src()
    i = s.index(name + " = [")
    return s[i:s.index("\n]", i)]


def test_har_qismda_exam_tegi():
    for name in ("IELTS_PARTS", "READING_TYPES"):
        b = _blok(name)
        kinds = len(re.findall(r'\{"kind":', b))
        exams = len(re.findall(r'"exam":', b))
        assert kinds == exams, (name, kinds, exams)


def test_cefr_listening_olti_qism():
    """CEFR listening imtihonida 6 qism bor."""
    b = _blok("IELTS_PARTS")
    assert b.count('"exam": "cefr"') == 6, b.count('"exam": "cefr"')


def test_cefr_reading_besh_qism():
    """CEFR reading: 2 ta o'ziga xos + 3 ta IELTS bilan umumiy."""
    b = _blok("READING_TYPES")
    own = b.count('"exam": "cefr"')
    both = b.count('"exam": "both"')
    assert own == 2, own
    assert both == 3, both
    assert own + both == 5


def test_filtr_ishlaydi():
    s = _src()
    assert "def _exam_parts(" in s
    # ikkala endpoint ham exam qabul qilsin
    assert "def ielts_listening_parts(exam: str | None = None," in s
    assert "def ielts_reading_parts(exam: str | None = None," in s
    # va filtrdan o'tkazsin
    assert "_exam_parts(IELTS_PARTS, exam)" in s
    assert "_exam_parts(READING_TYPES, exam)" in s


def test_both_ikkala_royxatda():
    """'both' qismlari IELTS'da ham, CEFR'da ham ko'rinsin."""
    s = _src()
    i = s.index("def _exam_parts(")
    blok = s[i:i + 700]
    assert '(exam, "both")' in blok


def test_ekranda_cefr_kartalari_bor():
    fe = open("../src/pages/student/StudentIelts.tsx",
              encoding="utf-8").read()
    assert "CEFR Listening (Multilevel)" in fe
    assert "CEFR Reading (Multilevel)" in fe
    assert "/student/ielts/listening?exam=cefr" in fe
    assert "/student/ielts/reading?exam=cefr" in fe


def test_home_sahifalar_exam_ni_uzatadi():
    for f in ("StudentIeltsReadingHome.tsx",
              "StudentIeltsListeningHome.tsx"):
        fe = open("../src/pages/student/" + f, encoding="utf-8").read()
        assert 'sp.get("exam")' in fe, f
        assert '?exam=" + exam' in fe, f
        assert "isCefr" in fe, f
