# -*- coding: utf-8 -*-
"""CEFR Reading 2-qism — Matching People to Texts.

Kitob formati: sakkizta e'lon, beshta odam, uchta e'lon ortiqcha.

BU TURDA ENG XAVFLI XATO — IKKI TO'G'RI JAVOB. Agar ikkita e'lon
odamning hamma shartiga javob bersa, mashqning to'g'ri javobi
yo'q bo'lib qoladi va bola nima qilsa ham xato bo'ladi. Shuning
uchun har e'longa XUSUSIYAT TEGLARI berilgan va test ularni
solishtiradi:
  * to'g'ri e'lon odamning BARCHA shartlariga javob berishi;
  * qolgan yettitasi kamida BITTASIGA javob bermasligi shart.
"""
import cefr_read_match_seed as M


def test_soni():
    rows = M.build_rows()
    assert len(rows) == 100, len(rows)
    assert len(M.SETS) == 20, len(M.SETS)
    for st in M.SETS:
        assert len(st["notices"]) == 8, st["topic"]
        assert len(st["people"]) == 5, st["topic"]


def test_javob_hamma_shartga_mos():
    bad = []
    for st in M.SETS:
        for desc, need, idx in st["people"]:
            tags = st["notices"][idx][2]
            if not need <= tags:
                bad.append((st["topic"], desc[:30], need - tags))
    assert not bad, bad


def test_ikkinchi_togri_javob_yoq():
    """ENG MUHIM: faqat BITTA e'lon hamma shartga javob bersin."""
    bad = []
    for st in M.SETS:
        for desc, need, idx in st["people"]:
            others = [st["notices"][i][0]
                      for i, (_t, _x, g) in enumerate(st["notices"])
                      if i != idx and need <= g]
            if others:
                bad.append((st["topic"], desc[:30], others))
    assert not bad, bad


def test_har_odamga_boshqa_elon():
    for st in M.SETS:
        idxs = [i for _d, _n, i in st["people"]]
        assert len(set(idxs)) == 5, (st["topic"], idxs)


def test_uchta_elon_ortiqcha():
    for st in M.SETS:
        used = {i for _d, _n, i in st["people"]}
        assert len(set(range(8)) - used) == 3, st["topic"]


def test_odamda_kamida_ikki_shart():
    """Bitta shart bo'lsa mashq juda oson bo'lib qoladi."""
    bad = [(st["topic"], d[:30]) for st in M.SETS
           for d, need, _i in st["people"] if len(need) < 2]
    assert not bad, bad


def test_elon_sarlavhalari_noyob():
    for st in M.SETS:
        titles = [t for t, _x, _g in st["notices"]]
        assert len(set(titles)) == 8, st["topic"]


def test_ekranda_hamma_elon_bor():
    for k, lvl, pl, a, *_ in M.build_rows():
        assert len(pl["options"]) == 8, lvl
        assert a in pl["options"], (lvl, a)
        for let in "ABCDEFGH":
            assert f"{let}. " in pl["passage"], (lvl, let)


def test_darajalar():
    lv = sorted({r[1] for r in M.build_rows()})
    assert lv == list(range(1, 21)), lv


def test_backend_ulangan():
    src = open("student_app.py", encoding="utf-8").read()
    assert '"kind": "cefr_match"' in src
    assert "from cefr_read_match_seed import CEFR_MATCH_TIPS" in src
    m = open("main.py", encoding="utf-8").read()
    assert "from cefr_read_match_seed import seed_cefr_match" in m


def test_qoidalar():
    assert len(M.CEFR_MATCH_TIPS) >= 6
    txt = " ".join(a + b for a, b, c in M.CEFR_MATCH_TIPS).lower()
    assert "ortiqcha" in txt and "shart" in txt
