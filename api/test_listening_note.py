# -*- coding: utf-8 -*-
"""CEFR Listening 2-qism — Note Completion.

Bu tur uch xil buzilishi mumkin:
  1) javob matnda umuman yo'q bo'lishi (o'zimizdan qo'shilgan so'z);
  2) javob ikki so'z bo'lishi (kitob qoidasi: ONE WORD);
  3) javob "hour"/"day" kabi so'z bo'lishi — tekshiruvchi
     _ielts_norm o'lchov so'zlarini olib tashlaydi va javob bo'sh
     satrga aylanib, HAR QANDAY narsa to'g'ri sanalardi.
"""
import re
import listening_note_seed as N


def _norm(t):
    """student_app._ielts_norm bilan bir xil."""
    t = (t or "").upper()
    for ch in " -/.,:;'’ʻ":
        t = t.replace(ch, "")
    for w in ("POUNDS", "POUND", "MINUTES", "MINUTE", "HOURS", "HOUR",
              "WEEKS", "WEEK", "MONTHS", "MONTH", "DAYS", "DAY",
              "KILOMETRES", "KILOMETERS", "KM", "METRES", "METERS",
              "AM", "PM", "£", "$"):
        t = t.replace(w, "")
    return t


def test_soni():
    rows = N.build_rows()
    assert len(rows) == 102, len(rows)
    assert len(N.TALKS) == 17, len(N.TALKS)
    for t in N.TALKS:
        assert len(t["items"]) == 6, t["no"]


def test_javob_matnda_aynan_bor():
    """Eng muhim tekshiruv: javob ma'ruzada AYNAN aytilishi shart."""
    bad = []
    for t in N.TALKS:
        for line, ans in t["items"]:
            if not re.search(
                    r"(?<![\w'])" + re.escape(ans) + r"(?![\w'])",
                    t["say"], re.I):
                bad.append((t["no"], ans))
    assert not bad, bad


def test_javob_bitta_soz():
    """Kitob qoidasi: ONE WORD and/or A NUMBER."""
    bad = [(t["no"], a) for t in N.TALKS for _l, a in t["items"]
           if len(a.split()) != 1]
    assert not bad, bad


def test_javob_bosh_satrga_aylanmaydi():
    """'hour', 'day' kabi javoblar taqiqlanadi — ular
    normalizatsiyadan keyin bo'sh qoladi va tekshiruv buziladi."""
    bad = [(t["no"], a) for t in N.TALKS for _l, a in t["items"]
           if not _norm(a)]
    assert not bad, bad


def test_qatorda_bitta_boshliq():
    for t in N.TALKS:
        for line, ans in t["items"]:
            assert line.count("%s") == 1, (t["no"], line)


def test_ekranda_butun_qaydnoma():
    for k, st, pl, a, *_ in N.build_rows():
        assert pl["prompt"].count(N.GAP) == 6, pl["order"]
        assert pl["prompt"].count("▶") == 1, pl["order"]
        assert pl["title"] in pl["prompt"], pl["order"]
        # Javob ekranda ko'rinmasin. BUTUN SO'Z sifatida
        # tekshiriladi: "art" javobi "start" ichida uchrashi
        # sizib chiqish emas.
        assert not re.search(
            r"(?<![\w'])" + re.escape(a) + r"(?![\w'])",
            pl["prompt"], re.I), (pl["order"], a)


def test_maruza_ekranda_korinmaydi():
    for k, st, pl, a, *_ in N.build_rows():
        assert pl["say"], pl["order"]
        assert pl["say"] not in pl["prompt"], pl["order"]
        assert len(pl["say"]) > 800, (pl["order"], len(pl["say"]))


def test_belgilangan_boshliq_togri():
    """▶ aynan gap_no qatorida turishi kerak."""
    for k, st, pl, a, *_ in N.build_rows():
        for line in pl["prompt"].split("\n"):
            if line.startswith("▶"):
                assert line.startswith(f"▶ ({pl['gap_no']})"), \
                    (pl["order"], line)


def test_bosqichlar():
    steps = sorted({r[1] for r in N.build_rows()})
    assert steps == [1, 2, 3, 4, 5], steps


def test_backend_ulangan():
    src = open("student_app.py", encoding="utf-8").read()
    assert '"kind": "cefr_note"' in src
    assert '"cefr_note",' in src
    assert "whitespace-pre-line" in open(
        "../src/pages/student/StudentIeltsListening.tsx",
        encoding="utf-8").read()
    m = open("main.py", encoding="utf-8").read()
    assert "from listening_note_seed import seed_note" in m


def test_qoidalar():
    assert len(N.NOTE_TIPS) >= 6
    txt = " ".join(a + b for a, b, c in N.NOTE_TIPS).lower()
    assert "tartib" in txt
