# -*- coding: utf-8 -*-
"""CEFR Reading 1-qism — Word From the Text.

Kitob qoidasi: "Fill in each gap with ONE word. You must use a word
which is somewhere in the rest of the text."

Bu qoida buzilsa mashq YECHIB BO'LMAYDIGAN bo'lib qoladi — bola
so'zni matndan qidiradi va topolmaydi. Shuning uchun bo'shliqlar
qo'lda emas, DASTUR bilan tanlanadi va test buni tasdiqlaydi.
"""
import re
import cefr_read_gap_seed as C


def test_soni():
    rows = C.build_rows()
    assert len(rows) == 100, len(rows)
    assert len(C.TEXTS) == 20, len(C.TEXTS)


def test_javob_matnda_bor():
    """ENG MUHIM: javob so'zi bo'shliqli matnda ham qoladi."""
    bad = []
    for k, lvl, pl, a, *_ in C.build_rows():
        if not re.search(r"(?<![A-Za-z])" + re.escape(a)
                         + r"(?![A-Za-z])", pl["passage"], re.I):
            bad.append((lvl, a))
    assert not bad, bad


def test_javob_bitta_soz():
    bad = [(l, a) for k, l, pl, a, *_ in C.build_rows()
           if len(a.split()) != 1]
    assert not bad, bad


def test_har_matnda_5_boshliq():
    for k, lvl, pl, a, *_ in C.build_rows():
        assert pl["passage"].count(C.GAP) == 5, (lvl, pl["gap_no"])
        for i in range(1, 6):
            assert f"({i}) " in pl["passage"], (lvl, i)


def test_bir_matnda_javoblar_har_xil():
    by = {}
    for k, lvl, pl, a, *_ in C.build_rows():
        by.setdefault(lvl, []).append(a.lower())
    for lvl, ans in by.items():
        assert len(set(ans)) == 5, (lvl, ans)


def test_javob_yordamchi_soz_emas():
    """'the', 'and' kabi so'zlar bo'shliqqa tushmasin — ular
    mashqni ma'nosiz qiladi."""
    bad = [(l, a) for k, l, pl, a, *_ in C.build_rows()
           if a.lower() in C.STOP or len(a) < 4]
    assert not bad, bad


def test_matnlar_yetarli_uzun():
    for t in C.TEXTS:
        assert 500 <= len(t["text"]) <= 1200, (t["title"],
                                               len(t["text"]))


def test_darajalar():
    lv = sorted({r[1] for r in C.build_rows()})
    assert lv == list(range(1, 21)), lv


def test_backend_ulangan():
    src = open("student_app.py", encoding="utf-8").read()
    assert '"kind": "cefr_word"' in src
    assert '"cefr_word")' in src          # READING_TYPED
    assert "from cefr_read_gap_seed import CEFR_WORD_TIPS" in src
    m = open("main.py", encoding="utf-8").read()
    assert "from cefr_read_gap_seed import seed_cefr_word" in m


def test_qoidalar():
    assert len(C.CEFR_WORD_TIPS) >= 6
    txt = " ".join(a + b for a, b, c in C.CEFR_WORD_TIPS).lower()
    assert "boshqa joyida" in txt
