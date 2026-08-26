# -*- coding: utf-8 -*-
"""Uchta tuzatish: writing tushuntirishi, writing soni, lug'at
xatolari.

Jahongir:
  1) "Writingda notogri javob yozsa togri gapni korsatib nega u
     yozgan javob xato va nega togri javob togriligini tushuntirish
     kerak va davom etish tugmasini bossagina keyingisiga o'tishi
     kerak."
  2) "Writingda qayta tuzsidha ham faqat 4ta chiqaryabdi mashqni.
     10ta tanlasa 10ta berish kerak 20ta tanlasansa 20ta."
  3) "100ta sozni qildi ichida 10ta soz xato bolsa, oxirida xato
     qilganlarni yana bir martadan korsatsin."
"""
import collections
import writing_seed2 as W


# ---------------- 2) Writing soni ----------------
def test_har_darajada_kamida_20_mashq():
    """20 tanlansa ham yetsin (avval 4 tadan edi)."""
    import practice_seed as P
    c = collections.Counter(x[0] for x in P._W_TRANSFORM)
    c.update(x[0] for x in W.W2)
    for lv in ("A1", "A2", "B1", "B2", "C1", "C2"):
        assert c[lv] >= 20, (lv, c[lv])


def test_yangi_toplam_tuzilishi():
    for row in W.W2:
        assert len(row) == 6, row[:2]
        lvl, instr, given, ans, alt, expl = row
        assert lvl in ("A1", "A2", "B1", "B2", "C1", "C2"), lvl
        assert instr.endswith(":"), instr
        assert given and ans and expl, row[:2]
        assert isinstance(alt, list)


def test_berilgan_va_javob_har_xil():
    """Javob berilgan gapning aynan nusxasi bo'lmasin."""
    bad = [g for _l, _i, g, a, _al, _e in W.W2
           if g.strip().lower().rstrip(".") == a.strip().lower()]
    assert not bad, bad


def test_korsatmalar_takrorlanmaydi_bir_darajada():
    """Bir darajada bir xil (ko'rsatma + berilgan) bo'lmasin."""
    seen = set()
    dup = []
    for lvl, instr, given, *_ in W.W2:
        k = (lvl, instr, given)
        if k in seen:
            dup.append(k)
        seen.add(k)
    assert not dup, dup


def test_seed_alohida_marker():
    src = open("writing_seed2.py", encoding="utf-8").read()
    assert '"writing_v2"' in src
    m = open("main.py", encoding="utf-8").read()
    assert "from writing_seed2 import seed_writing2" in m


# ---------------- 1) Writing tushuntirishi ----------------
def _fb():
    """student_app dagi _writing_feedback'ni alohida yuklaymiz."""
    src = open("student_app.py", encoding="utf-8").read()
    i = src.index("def _lev(")
    j = src.index("GRAMMAR_LANGS =")
    ns = {}
    exec("def _norm_loose(t):\n"
         "    t=(t or '').strip().lower()\n"
         "    for ch in \".,!?;:'-\":\n"
         "        t=t.replace(ch,' ')\n"
         "    return ' '.join(t.split())\n" + src[i:j], ns)
    return ns["_writing_feedback"]


def test_xato_turlari_aniqlanadi():
    f = _fb()
    # to'g'ri javobda tushuntirish yo'q
    assert f("I like tea", "I like tea") == ""
    # so'z tartibi
    assert "TARTIBI" in f("tea like I", "I like tea")
    # tushib qolgan so'z
    assert "tushib qolgan" in f("I like tea coffee",
                               "I like tea and coffee")
    # ortiqcha so'z
    assert "ortiqcha" in f("I like the tea", "I like tea")
    # fe'l shakli
    assert "SHAKLI" in f("She go home", "She goes home")
    # imlo
    assert "IMLO" in f("I recieved it", "I received it")
    # bo'sh javob
    assert "bo'sh" in f("", "I like tea")


def test_endpoint_why_qaytaradi():
    src = open("student_app.py", encoding="utf-8").read()
    assert src.count('"why": why') == 2, "ikkala tarmoqda ham kerak"
    assert "_writing_feedback(given, expected" in src
    assert 'skill != "writing"' in src


def test_ekran_tushuntirishni_korsatadi():
    fe = open("../src/pages/student/StudentPractice.tsx",
              encoding="utf-8").read()
    assert "result.why" in fe
    assert "Siz yozdingiz" in fe
    # xato javobda AVTOMATIK o'tmasin
    assert 'skill === "writing" && !r.correct' in fe
    assert "Tushundim, davom etish" in fe


# ---------------- 3) Lug'at xatolari ----------------
def test_lugat_xatolarni_qayta_soraydi():
    fe = open("../src/pages/student/StudentGamePlay.tsx",
              encoding="utf-8").read()
    assert "wrongIds" in fe
    assert '"main" | "bridge" | "retry"' in fe
    assert "startRetry" in fe
    assert "Xatolar ustida ishlash" in fe
    # xato bo'lsa so'z ro'yxatga qo'shilsin
    assert "setWrongIds((w) =>" in fe
    # ikkinchi bosqichda faqat xatolar
    assert "wrongIds.includes(it.word_id)" in fe
