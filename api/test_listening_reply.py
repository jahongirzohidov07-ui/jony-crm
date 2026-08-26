# -*- coding: utf-8 -*-
"""CEFR Listening 1-qism — Choose the Correct Reply.

Bu tur ikki xil buzilishi mumkin:
  1) to'g'ri javob doim bitta harfda turib qolishi (tinglamasdan
     100% olish mumkin bo'lardi);
  2) aytilgan gapning ekranda ko'rinib qolishi (tinglash mashqi
     o'qish mashqiga aylanardi).
Test ikkalasini ham tutadi.
"""
import listening_reply_seed as R


def test_soni():
    """100 ta o'zimiznikidan + 104 ta kitobdan (Multilevel Master
    audioskripti, Part 1, 1-13 mashqlar)."""
    rows = R.build_rows()
    assert len(rows) == 204, len(rows)
    own = [r for r in rows if not r[2]["book"]]
    book = [r for r in rows if r[2]["book"]]
    assert len(own) == 100, len(own)
    assert len(book) == 104, len(book)
    per = {}
    for k, st, pl, a, e, al, pa in own:
        per[st] = per.get(st, 0) + 1
    assert per == {1: 20, 2: 20, 3: 20, 4: 20, 5: 20}, per


def test_kitob_gaplari_aynan():
    """Audioskriptdagi gaplar o'zgartirilmasin."""
    rows = {r[2]["say"] for r in R.build_rows() if r[2]["book"]}
    kerak = [
        "How are you?",
        "Shall I retell the text?",
        "We went to Berlin last weekend.",
        "Bread is not taken with fork, is it?",
        "You go in for sports, don't you?",
        "Shall we have a snack lunch in a pub for a change?",
        "How far is it to Manchester?",
    ]
    yoq = [x for x in kerak if x not in rows]
    assert not yoq, yoq


def test_kitob_izohida_manba_bor():
    for k, st, pl, a, expl, *_ in R.build_rows():
        if pl["book"]:
            assert "audioskript" in expl.lower(), (st, expl)


def test_kitobniki_keyin_keladi():
    """Bir bosqich ichida avval o'zimizniki (tayyorgarlik), keyin
    kitobniki (haqiqiy imtihon gapi)."""
    for k, st, pl, *_ in R.build_rows():
        if pl["book"]:
            assert pl["order"] >= 100, (st, pl["order"])
        else:
            assert pl["order"] < 100, (st, pl["order"])


def test_har_savolda_3_variant():
    for k, st, pl, ans, *_ in R.build_rows():
        assert len(pl["options"]) == 3, (st, pl["say"])
        assert ans in pl["options"], (st, ans)
        bare = [o.split(". ", 1)[1].strip().lower()
                for o in pl["options"]]
        assert len(set(bare)) == 3, (st, bare)


def test_javob_harflari_tekis():
    """Tinglamasdan «hamma vaqt A» hiylasi ishlamasin."""
    cnt = {"A": 0, "B": 0, "C": 0}
    for k, st, pl, ans, *_ in R.build_rows():
        cnt[ans[0]] += 1
    tot = sum(cnt.values())
    for c, n in cnt.items():
        assert 0.28 <= n / tot <= 0.39, (c, n, cnt)


def test_aytilgan_gap_ekranda_korinmaydi():
    """payload'da say bor (TTS uchun), lekin prompt YO'Q —
    student_app faqat IELTS_WITH_PROMPT turlarida prompt yuboradi,
    ielts_reply u yerda emas."""
    for k, st, pl, *_ in R.build_rows():
        assert pl["say"], st
        assert "prompt" not in pl, st
    src = open("student_app.py", encoding="utf-8").read()
    i = src.index("IELTS_WITH_PROMPT = (")
    j = src.index(")", i)
    assert "ielts_reply" not in src[i:j], \
        "ielts_reply IELTS_WITH_PROMPT ichida — gap ekranda chiqadi!"


def test_ikki_marta_aytiladi():
    """Jahongir: '2 marta aytiladi CEFRdagi barcha listeninglar'."""
    for k, st, pl, *_ in R.build_rows():
        assert pl["plays"] == 2, (st, pl)
        assert pl["gap_ms"] >= 1000, (st, pl)
    src = open("../src/pages/student/StudentIeltsListening.tsx",
               encoding="utf-8").read()
    assert "q.plays || 1" in src
    assert "marta aytiladi" in src


def test_tezlik_bosqichma_bosqich():
    """Sekindan imtihon tezligigacha."""
    rate = {}
    for k, st, pl, *_ in R.build_rows():
        rate.setdefault(st, set()).add(pl["rate"])
    vals = [max(rate[i]) for i in sorted(rate)]
    assert vals == sorted(vals), vals
    assert vals[0] <= 0.75 and vals[-1] >= 1.0, vals


def test_izohda_gap_va_harf_bor():
    for k, st, pl, ans, expl, *_ in R.build_rows():
        assert f"To'g'ri javob: {ans[0]}." in expl, (st, expl)
        assert pl["say"] in expl, (st, expl)


def test_backend_ulangan():
    src = open("student_app.py", encoding="utf-8").read()
    assert '"kind": "ielts_reply"' in src
    assert 'IELTS_CHOICE = ("ielts_exact", "ielts_reply")' in src
    assert '"plays": pl.get("plays", 1)' in src
    m = open("main.py", encoding="utf-8").read()
    assert "from listening_reply_seed import seed_reply" in m


def test_bitta_mashqda_8ta():
    """Jahongir: 'bitta mashqda 8ta bolsin'."""
    src = open("../src/pages/student/StudentIeltsListening.tsx",
               encoding="utf-8").read()
    assert '[8, "8 ta"' in src


def test_qoidalar():
    assert len(R.REPLY_TIPS) >= 8
    txt = " ".join(a + b for a, b, c in R.REPLY_TIPS).lower()
    for kerak in ("needn't", "so do i", "wh-", "yordamchi"):
        assert kerak in txt, kerak
