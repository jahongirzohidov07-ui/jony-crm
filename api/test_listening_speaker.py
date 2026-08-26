# -*- coding: utf-8 -*-
"""CEFR Listening 3-qism — Matching Speakers.

Bu tur uch xil buzilishi mumkin:
  1) manbada 1-so'zlovchi A, 2-si B ... bo'lgani uchun javoblar
     ketma-ket harflarga tushib qolishi (tinglamasdan 100%);
  2) bitta mashqda ikki so'zlovchiga bir xil variant berilishi
     (imtihonda variant takrorlanmaydi);
  3) so'zlovchi nutqining ekranda ko'rinib qolishi.
"""
import listening_speaker_seed as S


def _in_choice(kind):
    """IELTS_CHOICE ro'yxati ichida shu tur bormi. Ro'yxat har
    yangi CEFR qismida o'sadi, shuning uchun qattiq satr emas."""
    src = open("student_app.py", encoding="utf-8").read()
    i = src.index("IELTS_CHOICE = (")
    return kind in src[i:src.index(")", i)]


def test_soni():
    rows = S.build_rows()
    assert len(rows) == 100, len(rows)
    assert len(S.SETS) == 20, len(S.SETS)
    for st in S.SETS:
        assert len(st["speakers"]) == 5, st["no"]
        assert len(st["options"]) == 7, st["no"]
        assert len(st["answers"]) == 5, st["no"]


def test_bir_mashqda_variant_takrorlanmaydi():
    """Imtihon qoidasi: bir variant ikki so'zlovchiga berilmaydi."""
    for st in S.SETS:
        assert len(set(st["answers"])) == 5, st["no"]


def test_ikkita_ortiqcha_variant():
    """7 variant, 5 tasi ishlatiladi -> aynan 2 tasi ortiqcha."""
    for st in S.SETS:
        ishlatilgan = set(st["answers"])
        assert len(set(range(7)) - ishlatilgan) == 2, st["no"]


def test_javoblar_ketma_ket_emas():
    """A B C D E tartibida tushib qolmasin."""
    by = {}
    for k, step, pl, ans, *_ in S.build_rows():
        by.setdefault(pl["order"] // 10, []).append(ans[0])
    for no, lets in by.items():
        assert len(lets) == 5, no
        idx = [S.LET.index(x) for x in lets]
        assert idx != sorted(idx) or len(set(idx)) < 5 or \
            idx != list(range(idx[0], idx[0] + 5)), (no, lets)
        # eng muhimi: A,B,C,D,E bo'lib qolmasin
        assert lets != ["A", "B", "C", "D", "E"], (no, lets)


def test_harflar_bir_joyga_toplanmagan():
    c = {}
    for k, step, pl, ans, *_ in S.build_rows():
        c[ans[0]] = c.get(ans[0], 0) + 1
    tot = sum(c.values())
    for let, n in c.items():
        assert n / tot <= 0.22, (let, n, c)
        assert n / tot >= 0.08, (let, n, c)


def test_nutq_ekranda_korinmaydi():
    """say — faqat TTS uchun. prompt'da mavzu va Speaker N bor,
    nutqning o'zi YO'Q."""
    for k, step, pl, ans, *_ in S.build_rows():
        assert pl["say"], pl["order"]
        assert pl["say"] not in pl["prompt"], pl["order"]
        assert "Speaker" in pl["prompt"], pl["order"]


def test_javob_variantlar_ichida():
    for k, step, pl, ans, *_ in S.build_rows():
        assert ans in pl["options"], (pl["order"], ans)
        bare = [o.split(". ", 1)[1] for o in pl["options"]]
        assert len(set(bare)) == 7, pl["order"]


def test_nutqlar_uzunligi_real():
    """Kitobdan olingan nutqlar qirqilib qolmagan."""
    for st in S.SETS:
        for sp in st["speakers"]:
            assert 250 <= len(sp) <= 1200, (st["no"], len(sp))
            assert not sp.startswith((":", "Man:", "Woman:")), st["no"]


def test_bosqichlar():
    steps = sorted({r[1] for r in S.build_rows()})
    assert steps == [1, 2, 3, 4, 5], steps


def test_backend_ulangan():
    src = open("student_app.py", encoding="utf-8").read()
    assert '"kind": "cefr_speaker"' in src
    assert _in_choice("cefr_speaker")
    assert 'IELTS_WITH_PROMPT = ("cefr_speaker",' in src
    m = open("main.py", encoding="utf-8").read()
    assert "from listening_speaker_seed import seed_speaker" in m


def test_qoidalar():
    assert len(S.SPEAKER_TIPS) >= 6
    txt = " ".join(a + b for a, b, c in S.SPEAKER_TIPS).lower()
    assert "ortiqcha" in txt
    assert "parafraz" in txt
