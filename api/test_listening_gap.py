# -*- coding: utf-8 -*-
"""CEFR Listening 6-qism — Sentence Completion."""
import re
import listening_gap_seed as G


def _norm(t):
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
    rows = G.build_rows()
    assert len(rows) == 102, len(rows)
    assert len(G.TALKS) == 17
    for t in G.TALKS:
        assert len(t["items"]) == 6, t["no"]


def test_javob_matnda_aynan_bor():
    bad = []
    for t in G.TALKS:
        for line, ans in t["items"]:
            if not re.search(
                    r"(?<![A-Za-z0-9])" + re.escape(ans)
                    + r"(?![A-Za-z0-9])", t["say"], re.I):
                bad.append((t["no"], ans))
    assert not bad, bad


def test_javob_bitta_soz():
    bad = [(t["no"], a) for t in G.TALKS for _l, a in t["items"]
           if len(a.split()) != 1]
    assert not bad, bad


def test_javob_bosh_satrga_aylanmaydi():
    bad = [(t["no"], a) for t in G.TALKS for _l, a in t["items"]
           if not _norm(a)]
    assert not bad, bad


def test_ekranda_javob_korinmaydi():
    for k, st, pl, a, *_ in G.build_rows():
        assert pl["prompt"].count(G.GAP) == 6, pl["order"]
        assert pl["prompt"].count("▶") == 1, pl["order"]
        # Qator RAQAMINI tashlab tekshiramiz: "5." javobi "5" ga
        # o'xshab ketadi, lekin bu sizib chiqish emas.
        body = "\n".join(
            re.sub(r"^[▶ ]*\d+\.\s*", "", ln)
            for ln in pl["prompt"].split("\n"))
        assert not re.search(
            r"(?<![A-Za-z0-9])" + re.escape(a) + r"(?![A-Za-z0-9])",
            body, re.I), (pl["order"], a)


def test_maruza_uzun_va_yashirin():
    for k, st, pl, a, *_ in G.build_rows():
        assert len(pl["say"]) > 1500, (pl["order"], len(pl["say"]))
        assert pl["say"] not in pl["prompt"], pl["order"]


def test_maruzalar_2qismdan_uzunroq():
    """6-qism 2-qismdan jiddiy uzunroq bo'lishi kerak."""
    import listening_note_seed as N
    o6 = sum(len(t["say"]) for t in G.TALKS) / len(G.TALKS)
    o2 = sum(len(t["say"]) for t in N.TALKS) / len(N.TALKS)
    assert o6 > o2 * 1.2, (o2, o6)


def test_jingalak_apostrof_yoq():
    """TTS va javob tekshiruvi uchun apostrof bir xil bo'lsin."""
    for t in G.TALKS:
        assert "’" not in t["say"], t["no"]


def test_belgilangan_gap_togri():
    for k, st, pl, a, *_ in G.build_rows():
        for line in pl["prompt"].split("\n"):
            if line.startswith("▶"):
                assert line.startswith(f"▶ {pl['gap_no']}."), \
                    (pl["order"], line)


def test_bosqichlar():
    assert sorted({r[1] for r in G.build_rows()}) == [1, 2, 3, 4, 5]


def test_backend_ulangan():
    src = open("student_app.py", encoding="utf-8").read()
    assert '"kind": "cefr_gap"' in src
    assert '"cefr_gap",' in src
    m = open("main.py", encoding="utf-8").read()
    assert "from listening_gap_seed import seed_gap" in m


def test_qoidalar():
    assert len(G.GAP_TIPS) >= 6
