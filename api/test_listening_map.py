# -*- coding: utf-8 -*-
"""CEFR Listening 4-qism — Map Labelling.

ENG MUHIM TEKSHIRUV. Xarita ham, ma'ruza ham shu loyihada
tuzilgani uchun ikkalasining MOSLIGINI dastur tekshira oladi:
har joyning harfi xaritada qayerda tursa, ma'ruzada ham aynan
o'sha joylashuv aytilgan bo'lishi kerak. Masalan javob A bo'lsa,
ma'ruzada "north-west" so'zi shu joy haqidagi gapda turishi shart.
Bu tekshiruvsiz "xarita bir narsa deydi, audio boshqa narsa"
degan xato sezilmay qolardi.
"""
import re
import listening_map_seed as M


def _sentences(t):
    return re.split(r"(?<=[.!?])\s+", t)


def _place_sentence(say, name):
    """Joy nomi aytilgan gapni (va undan keyingisini) qaytaradi."""
    ss = _sentences(say)
    key = name.replace("the ", "").replace("'", "'")
    for i, s in enumerate(ss):
        if key.lower() in s.lower():
            return " ".join(ss[i:i + 2])
    return ""


def test_soni():
    rows = M.build_rows()
    assert len(rows) == 100, len(rows)
    assert len(M.SITES) == 20, len(M.SITES)
    for s in M.SITES:
        assert len(s["places"]) == 5, s["no"]


def test_joylar_maruzada_aytilgan():
    bad = []
    for s in M.SITES:
        for name, let in s["places"]:
            if not _place_sentence(s["say"], name):
                bad.append((s["no"], name))
    assert not bad, bad


def test_xarita_va_maruza_MOS():
    """Harf xaritada qayerda tursa, ma'ruzada ham shunday aytilsin."""
    bad = []
    for s in M.SITES:
        table = (M.COMPASS_POS if s["shape"] == "compass"
                 else M.CORRIDOR_POS)
        for name, let in s["places"]:
            sent = _place_sentence(s["say"], name).lower()
            kerak = table.get(let, [])
            if not any(k.lower() in sent for k in kerak):
                bad.append((s["no"], name, let, sent[:90]))
    assert not bad, bad


def test_harflar_takrorlanmaydi():
    """Bitta xaritada bir harf ikki joyga berilmasin."""
    for s in M.SITES:
        lets = [l for _n, l in s["places"]]
        assert len(set(lets)) == 5, (s["no"], lets)


def test_ortiqcha_variant_bor():
    """Kitob qoidasi: ishlatilmaydigan harflar bo'lishi shart."""
    for k, st, pl, a, *_ in M.build_rows():
        assert len(pl["options"]) >= 7, pl["order"]
        assert a in pl["options"], pl["order"]


def test_xarita_toliq():
    for s in M.SITES:
        for let in "ABCDEFGH":
            if let in [l for _n, l in s["places"]]:
                assert let in s["figure"], (s["no"], let)
        assert s["figure"].count("\n") >= 6, s["no"]


def test_maruza_ekranda_korinmaydi():
    for k, st, pl, a, *_ in M.build_rows():
        assert pl["say"] not in pl["prompt"], pl["order"]
        assert pl["prompt"].startswith(
            pl["prompt"].split("  —  ")[0]), pl["order"]
        assert "Where is" in pl["prompt"], pl["order"]


def test_javob_ekranda_yozilmagan():
    """Xaritada faqat harflar bo'lsin — joy nomi yozilmasin."""
    for s in M.SITES:
        for name, let in s["places"]:
            k = name.replace("the ", "")
            assert k.lower() not in s["figure"].lower(), (s["no"], k)


def test_harflar_bir_joyga_toplanmagan():
    c = {}
    for k, st, pl, a, *_ in M.build_rows():
        c[a] = c.get(a, 0) + 1
    tot = sum(c.values())
    for let, n in c.items():
        assert n / tot <= 0.20, (let, n, c)


def test_bosqichlar():
    assert sorted({r[1] for r in M.build_rows()}) == [1, 2, 3, 4, 5]


def test_qoidalar():
    assert len(M.MAP_TIPS) >= 6
    txt = " ".join(a + b for a, b, c in M.MAP_TIPS).lower()
    assert "north" in txt and "ortiqcha" in txt


def test_backend_ulangan():
    src = open("student_app.py", encoding="utf-8").read()
    assert '"kind": "cefr_map"' in src
    i = src.index("IELTS_CHOICE = (")
    assert "cefr_map" in src[i:src.index(")", i)]
    assert '"figure": pl.get("figure")' in src
    fe = open("../src/pages/student/StudentIeltsListening.tsx",
              encoding="utf-8").read()
    assert "q.figure" in fe and "font-mono" in fe
    m = open("main.py", encoding="utf-8").read()
    assert "from listening_map_seed import seed_map" in m
