# -*- coding: utf-8 -*-
"""CEFR Listening 5-qism — Three Extracts (A/B/C)."""
import listening_extract_seed as E


def test_soni():
    rows = E.build_rows()
    assert len(rows) == 102, len(rows)
    assert len(E.EXTRACTS) == 51, len(E.EXTRACTS)
    for x in E.EXTRACTS:
        assert len(x["qs"]) == 2, (x["no"], x["idx"])


def test_har_parchada_ikkita_savol():
    """Kitob qoidasi: har parchaga AYNAN ikkita savol."""
    by = {}
    for k, st, pl, a, *_ in E.build_rows():
        by.setdefault(pl["order"] // 10, []).append(pl["prompt"])
    for key, qs in by.items():
        assert len(qs) == 2, (key, qs)
        assert qs[0] != qs[1], key


def test_javob_harflari_teng():
    c = {"A": 0, "B": 0, "C": 0}
    for k, st, pl, a, *_ in E.build_rows():
        c[a[0]] += 1
    tot = sum(c.values())
    for let, n in c.items():
        assert 0.28 <= n / tot <= 0.39, (let, n, c)


def test_uchta_noyob_variant():
    for k, st, pl, a, *_ in E.build_rows():
        assert len(pl["options"]) == 3, pl["order"]
        assert a in pl["options"], pl["order"]
        bare = [o.split(". ", 1)[1].strip().lower()
                for o in pl["options"]]
        assert len(set(bare)) == 3, (pl["order"], bare)


def test_parcha_ekranda_korinmaydi():
    """say faqat TTS uchun; prompt'da savol bor, parcha yo'q."""
    for k, st, pl, a, *_ in E.build_rows():
        assert pl["say"], pl["order"]
        assert pl["say"] not in pl["prompt"], pl["order"]
        assert pl["prompt"].startswith("Extract "), pl["order"]


def test_parchalar_kitobdan_toliq():
    for x in E.EXTRACTS:
        assert 400 <= len(x["say"]) <= 1500, (x["no"], len(x["say"]))
        assert "[" not in x["say"], x["no"]


def test_savol_belgisi():
    for x in E.EXTRACTS:
        for q, opts, ci in x["qs"]:
            assert q.endswith("?"), (x["no"], q)
            assert 0 <= ci <= 2, (x["no"], ci)


def test_bosqichlar():
    steps = sorted({r[1] for r in E.build_rows()})
    assert steps == [1, 2, 3, 4, 5], steps


def test_backend_ulangan():
    src = open("student_app.py", encoding="utf-8").read()
    assert '"kind": "cefr_extract"' in src
    i = src.index("IELTS_CHOICE = (")
    assert "cefr_extract" in src[i:src.index(")", i)]
    assert 'IELTS_WITH_PROMPT = ("cefr_speaker", "cefr_extract",' in src
    m = open("main.py", encoding="utf-8").read()
    assert "from listening_extract_seed import seed_extract" in m


def test_qoidalar():
    assert len(E.EXTRACT_TIPS) >= 6
    txt = " ".join(a + b for a, b, c in E.EXTRACT_TIPS).lower()
    assert "xulosa" in txt
