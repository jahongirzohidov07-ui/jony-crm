# -*- coding: utf-8 -*-
"""Pick from a List kontentini TUZILISH bo'yicha tekshiradi.

Bu test mazmunni emas, buzilishi mumkin bo'lgan narsalarni
tekshiradi: har savolda aynan 5 variant va aynan 2 to'g'ri javob
bormi, javoblar bir-biriga o'xshab qolmaganmi, to'g'ri javob
pozitsiyalari bir joyga to'planib qolmaganmi (MCQ'da aynan shu
xato chiqqan edi), matn qiyinlashib boryaptimi.
"""
import re
import reading_pick_seed as R


def test_soni_va_darajalari():
    rows = R.build_rows()
    assert len(rows) == 100, len(rows)
    lv = sorted({r[1] for r in rows})
    assert lv == list(range(1, 23)), lv


def test_har_savolda_5_variant_2_javob():
    for kind, lvl, pl, ans, expl, alt, para in R.build_rows():
        assert len(pl["options"]) == 5, (lvl, pl["prompt"])
        assert pl["pick"] == 2
        parts = [x.strip() for x in ans.split(R.SEP.strip()) if x.strip()]
        assert len(parts) == 2, (lvl, ans)
        # javoblar variantlar ichida bo'lishi shart
        for p in parts:
            assert p in pl["options"], (lvl, p)
        # ikkalasi har xil
        assert parts[0] != parts[1], (lvl, ans)


def test_variantlar_takrorlanmaydi():
    """Bitta savolda ikki bir xil variant bo'lmasin."""
    for kind, lvl, pl, ans, *_ in R.build_rows():
        bare = [o.split(". ", 1)[1].strip().lower().rstrip(".")
                for o in pl["options"]]
        assert len(set(bare)) == 5, (lvl, pl["prompt"], bare)


def test_javob_juftliklari_tarqoq():
    """MCQ'da to'g'ri javob 72% B chiqib qolgan edi. Bu yerda
    ikkita javob bo'lgani uchun HAR HARF nechta savolda javob
    bo'lganini sanaymiz — hech biri 35% dan oshmasin."""
    cnt = {c: 0 for c in R.LET}
    for kind, lvl, pl, ans, *_ in R.build_rows():
        for p in ans.split(R.SEP.strip()):
            cnt[p.strip()[0]] += 1
    tot = sum(cnt.values())
    assert tot == 200, tot
    for c, n in cnt.items():
        assert n / tot <= 0.35, (c, n, cnt)
        assert n / tot >= 0.10, (c, n, cnt)


def test_qiyinlashib_boradi():
    """Matn uzunligi umumiy o'sish tendensiyasida bo'lsin."""
    by = {}
    for p in R.PASSAGES:
        by[p["level"]] = len(p["text"])
    boshi = sum(by[i] for i in range(1, 9)) / 8
    orta = sum(by[i] for i in range(9, 17)) / 8
    oxiri = sum(by[i] for i in range(17, 23)) / 6
    assert boshi < orta < oxiri, (boshi, orta, oxiri)
    assert oxiri > boshi * 3


def test_izohda_javob_harflari_bor():
    for kind, lvl, pl, ans, expl, *_ in R.build_rows():
        a, b = [p.strip()[0] for p in ans.split(R.SEP.strip())]
        assert f"To'g'ri javob: {a} va {b}." in expl, (lvl, expl)
        assert "Matnda: " in expl


def test_iqtibos_matnda_bor():
    """Izohdagi «...» iqtibosining har bo'lagi matnda bo'lsin."""
    txt = {p["level"]: p["text"] for p in R.PASSAGES}
    bad = []
    for kind, lvl, pl, ans, expl, *_ in R.build_rows():
        m = re.search(r"«(.+?)»", expl)
        if not m:
            continue
        body = txt[lvl].replace("\n", " ")
        body = re.sub(r"\s+", " ", body)
        for chunk in m.group(1).split(" ... "):
            chunk = re.sub(r"\s+", " ", chunk).strip()
            if chunk and chunk not in body:
                bad.append((lvl, chunk[:60]))
    assert not bad, bad


def test_jahongir_namunalari():
    """Kitob kaliti bilan bir xil bo'lishi SHART."""
    want = {
        # 18 — On the trail of the honey badger
        (18, 1): "BD", (18, 2): "AB", (18, 3): "CD",
        (18, 4): "BD", (18, 5): "AE",
        # 20 — Humpback whale breaks migration record
        (20, 1): "BC", (20, 2): "CE", (20, 3): "AE", (20, 4): "AE",
        (20, 5): "BD", (20, 6): "AD", (20, 7): "BE",
    }
    got = {}
    for kind, lvl, pl, ans, *_ in R.build_rows():
        if lvl in (18, 20):
            got[(lvl, pl["order"])] = "".join(
                p.strip()[0] for p in ans.split(R.SEP.strip()))
    assert got == want, {k: (got.get(k), v)
                         for k, v in want.items() if got.get(k) != v}


def test_kitob_matnlari_qoyilgan():
    t = {p["level"]: p for p in R.PASSAGES}
    assert "honey badger" in t[18]["text"].lower()
    assert "Kitso Khama" in t[18]["text"]
    assert "humpback" in t[20]["text"].lower()
    assert "Madagascar" in t[20]["text"]
    # Whale — 7 savol (kitobda 1-14, ya'ni 7 juft)
    assert len(t[20]["qs"]) == 7


def test_qoidalar():
    assert len(R.PICK_TIPS) >= 6
    for a, b, c in R.PICK_TIPS:
        assert a and b


# =====================================================================
#  TO'LIQ OQIM — ikkita javobni tanlash haqiqatan ishlaydimi
# =====================================================================
def test_javob_tekshiruvi_toplam_sifatida():
    """student_app'dagi mantiqning aynan o'zi: tartib muhim emas,
    bittasi to'g'ri bo'lsa ball berilmaydi."""
    def pset(t):
        return {x.strip().upper()
                for x in (t or "").split(R.SEP.strip()) if x.strip()}

    for kind, lvl, pl, ans, *_ in R.build_rows()[:20]:
        parts = [x.strip() for x in ans.split(R.SEP.strip())]
        ok = lambda g: bool(pset(g)) and pset(g) == pset(ans)
        assert ok(R.SEP.join(parts)), lvl              # to'g'ri
        assert ok(R.SEP.join(reversed(parts))), lvl    # teskari tartib
        assert ok(R.SEP.join(parts).lower()), lvl      # registr
        assert not ok(parts[0]), lvl                   # bittasi — YO'Q
        assert not ok(""), lvl                         # bo'sh — YO'Q
        # uchtasi ham noto'g'ri
        uch = pl["options"][:3]
        if pset(R.SEP.join(uch)) != pset(ans):
            assert not ok(R.SEP.join(uch)), lvl


def test_student_app_ulangan():
    """Backend haqiqatan read_pick'ni to'plam sifatida tekshiradimi."""
    src = open("student_app.py", encoding="utf-8").read()
    assert 'read_pick' in src
    assert 'from reading_pick_seed import SEP' in src
    assert '"pick": pl.get("pick")' in src
    assert 'from reading_pick_seed import PICK_TIPS' in src
    m = open("main.py", encoding="utf-8").read()
    assert 'from reading_pick_seed import seed_pick' in m


def test_frontend_kop_tanlov():
    """Ekranda ikkita tanlash rejimi bormi va ajratgich bir xilmi."""
    src = open("../src/pages/student/StudentIeltsReading.tsx",
               encoding="utf-8").read()
    assert 'const PICK_SEP = " ||| ";' in src
    assert R.SEP == " ||| ", R.SEP     # backend bilan bir xil
    assert "toggleMulti" in src
    assert "need > 1" in src


def test_round_javobni_oshkor_qilmaydi():
    """Round javobni ham, javob harflarini ham yubormasligi kerak."""
    for kind, lvl, pl, ans, expl, *_ in R.build_rows():
        j = str(pl)
        assert "To'g'ri javob" not in j, lvl
        # payload ichida faqat variantlar bor, javob alohida ustunda
        assert "answer" not in pl
