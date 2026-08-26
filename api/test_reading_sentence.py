# -*- coding: utf-8 -*-
"""Sentence Completion kontentini tekshiradi.

Bu tur ikki xil buzilishi mumkin:
  1) javob matnda AYNAN yo'q (o'zimizdan so'z o'ylab topilgan);
  2) javob 2 so'zdan uzun (haqiqiy imtihonda nol ball).
Test ikkalasini ham tutadi. Yana: har gapda bitta bo'shliq, gap
matndagi jumlaning O'ZI emas (paraffraz), javoblar matn tartibida.
"""
import re
import reading_sentence_seed as S


def _flat(t):
    return re.sub(r"\s+", " ", t.replace("\n", " ")).strip()


def test_soni_va_darajalari():
    rows = S.build_rows()
    assert len(rows) == 100, len(rows)
    assert sorted({r[1] for r in rows}) == list(range(1, 21))


def test_javob_matnda_aynan_bor():
    """So'z sifatida (ichida emas) matnda uchrashi shart."""
    txt = {p["level"]: _flat(p["text"]) for p in S.PASSAGES}
    bad = []
    for kind, lvl, pl, ans, expl, alt, para in S.build_rows():
        body = txt[lvl]
        if not re.search(r"(?<![\w'])" + re.escape(ans) + r"(?![\w'])",
                         body, re.I):
            bad.append((lvl, ans))
    assert not bad, bad


def test_javob_ikki_sozdan_oshmaydi():
    bad = [(l, a) for k, l, p, a, e, al, pa in S.build_rows()
           if len(a.split()) > 2]
    assert not bad, bad


def test_bitta_boshliq():
    for kind, lvl, pl, *_ in S.build_rows():
        assert pl["prompt"].count(S.GAP) == 1, (lvl, pl["prompt"])


def test_gap_matndan_kochirilmagan():
    """Gap matndagi jumlaning aynan o'zi bo'lmasin — bu tur
    PARAFFRAZni o'rgatadi. Bo'shliqni javob bilan to'ldirib
    ko'ramiz: natija matnda uchramasligi kerak."""
    txt = {p["level"]: _flat(p["text"]).lower() for p in S.PASSAGES}
    bad = []
    for kind, lvl, pl, ans, *_ in S.build_rows():
        full = _flat(pl["prompt"].replace(S.GAP, ans)).lower()
        full = full.rstrip(".")
        if len(full) > 25 and full in txt[lvl]:
            bad.append((lvl, full[:70]))
    assert not bad, bad


def test_javoblar_matn_tartibida():
    """1-gapning javobi 2-gapnikidan oldin turishi kerak —
    qoidalarda shunday o'rgatiladi, demak amalda ham shunday
    bo'lsin."""
    bad = []
    for p in S.PASSAGES:
        body = _flat(p["text"]).lower()
        poz = []
        for sent, ans, alt, quote, note in p["items"]:
            q = _flat(quote).lower()[:60]
            poz.append(body.find(q))
        if any(x < 0 for x in poz):
            bad.append((p["level"], "iqtibos topilmadi", poz))
        elif poz != sorted(poz):
            bad.append((p["level"], poz))
    assert not bad, bad


def test_iqtibos_matnda_bor():
    txt = {p["level"]: _flat(p["text"]) for p in S.PASSAGES}
    bad = []
    for p in S.PASSAGES:
        for sent, ans, alt, quote, note in p["items"]:
            if _flat(quote).rstrip(".") not in txt[p["level"]]:
                bad.append((p["level"], _flat(quote)[:60]))
    assert not bad, bad


def test_qiyinlashib_boradi():
    by = {p["level"]: len(p["text"]) for p in S.PASSAGES}
    boshi = sum(by[i] for i in range(1, 7)) / 6
    orta = sum(by[i] for i in range(7, 16)) / 9
    oxiri = sum(by[i] for i in range(17, 21)) / 4
    assert boshi < orta < oxiri, (boshi, orta, oxiri)
    assert oxiri > boshi * 3


def test_jahongir_namunasi():
    """READING #20 The honey badger — 8 ta savol, kitobdagi javob."""
    p = [x for x in S.PASSAGES if x["level"] == 16][0]
    assert "honey badger" in p["text"].lower()
    assert "honeyguide" in p["text"]
    assert len(p["items"]) == 8
    want = ["aggressive", "humans", "instantly recognisable",
            "extremely varied", "small creatures", "smell",
            "special traps", "working relationship"]
    assert [it[1] for it in p["items"]] == want


def test_soz_sanash_qoidasi_oqitiladi():
    """«sense of smell» uch so'z — bu qoida albatta aytilishi
    kerak, chunki namunada aynan shu qopqon bor."""
    txt = " ".join(a + b + c for a, b, c in S.SENTENCE_TIPS).lower()
    assert "two words" in txt or "2 so'z" in txt
    hb = [x for x in S.PASSAGES if x["level"] == 16][0]
    smell = [it for it in hb["items"] if it[1] == "smell"][0]
    assert "uch so'z" in smell[4].lower()


def test_alt_javoblar_ham_matnda():
    txt = {p["level"]: _flat(p["text"]) for p in S.PASSAGES}
    bad = []
    for kind, lvl, pl, ans, expl, alt, para in S.build_rows():
        if alt and not re.search(
                r"(?<![\w'])" + re.escape(alt) + r"(?![\w'])",
                txt[lvl], re.I):
            bad.append((lvl, alt))
    assert not bad, bad


def test_qoidalar():
    assert len(S.SENTENCE_TIPS) >= 6
    for a, b, c in S.SENTENCE_TIPS:
        assert a and b


def test_backend_ulangan():
    src = open("student_app.py", encoding="utf-8").read()
    # 2026-08-26: qatordagi maydonlar orasiga "exam" qo'shildi,
    # shuning uchun yonma-yonlik emas, BITTA QATORDA borligi
    # tekshiriladi.
    qator = [q for q in src.splitlines() if '"read_sentence"' in q
             and '"Sentence Completion"' in q]
    assert qator, "READING_TYPES ichida read_sentence topilmadi"
    # Javob YOZILADI (variant tanlanmaydi) — READING_TYPED ichida.
    # Ro'yxat o'sib boryapti, shuning uchun qattiq satr emas.
    i = src.index("READING_TYPED = (")
    assert "read_sentence" in src[i:src.index(")", i)]
    assert 'from reading_sentence_seed import SENTENCE_TIPS' in src
    m = open("main.py", encoding="utf-8").read()
    assert 'from reading_sentence_seed import seed_sentence' in m


def test_javob_tekshiruvi_kechirimli():
    """_read_norm registr, tinish belgisi, defis va boshidagi
    artiklni e'tiborsiz qoldiradi — javob shu qoidaga mos yozilsin."""
    def norm(t):
        t = (t or "").strip().lower()
        for art in ("a ", "an ", "the "):
            if t.startswith(art):
                t = t[len(art):]
                break
        for ch in " ,.;:'’-–—":
            t = t.replace(ch, "")
        return t

    for kind, lvl, pl, ans, expl, alt, para in S.build_rows():
        assert norm(ans), (lvl, ans)
        # javob artikl bilan boshlanmasin (norm uni yeb qo'yadi)
        assert not ans.lower().startswith(("a ", "an ", "the ")), \
            (lvl, ans)
        if alt:
            assert norm(alt) != norm(ans), (lvl, ans, alt)
