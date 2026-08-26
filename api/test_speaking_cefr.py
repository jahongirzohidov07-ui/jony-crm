# -*- coding: utf-8 -*-
"""Multilevel Speaking — format, ball va kontent testlari (2026-08-26).

Jahongir: "speaking 0-75 ballgacha 65-75 C1 ga teng 51-64 bu B2ga
teng 30-50 B1 ga teng qolgani A1-A2 darajada, shunaqa darajada
0-75 orasida ballini hisoblab chiqarib berishing kerak."

Bu testlar ikki narsani qo'riqlaydi:
  1. FORMAT rasmiy hujjatdan chetga chiqmasligi (qismlar, savollar
     soni, soniyalar, tayyorgarlik vaqti).
  2. BALL SHKALASI Jahongir bergan chegaralarga aynan tushishi.

Va eng muhimi — test_namunalar_yuqori_ball(): har namuna javob O'Z
tahlilchimizdan o'tkaziladi. Kontent tahlilchini, tahlilchi
kontentni tekshiradi.
"""
import speaking_cefr_format as F
import speaking_cefr_seed as S
import speaking_cefr_guide as G


# =================================================================
#  1. FORMAT (speaking_format.pdf ga aynan mos bo'lishi kerak)
# =================================================================

def test_tort_qism():
    assert [p["part"] for p in F.PARTS] == ["1.1", "1.2", "2", "3"]


def test_savollar_soni_va_daraja():
    kutilgan = {"1.1": ("A1-A2", 3), "1.2": ("B1", 3),
                "2": ("B2", 3), "3": ("C1", 1)}
    for p in F.PARTS:
        lv, n = kutilgan[p["part"]]
        assert p["level"] == lv, p["part"]
        assert p["questions"] == n, p["part"]


def test_vaqt_taqsimoti():
    """PDF: 1.1 har savolga 30s; 1.2 4-savol 45s, 5-6 30s;
    2 va 3-qism 2 daqiqa + 1 daqiqa tayyorgarlik."""
    m = F.PART_BY_KEY
    assert m["p11"]["seconds"] == [30, 30, 30]
    assert m["p11"]["prep"] == 0
    assert m["p12"]["seconds"] == [45, 30, 30]
    assert m["p12"]["prep"] == 0
    assert m["p2"]["seconds"] == [120] and m["p2"]["prep"] == 60
    assert m["p3"]["seconds"] == [120] and m["p3"]["prep"] == 60


def test_bloklar_rasmiy_shkalaga_mos():
    """yangi_format_eng.pdf: Q1-3, Q4-6, Q7 -> 0-5; Q8 -> 0-6."""
    assert F.BANDS["q1_3"]["max"] == 5
    assert F.BANDS["q4_6"]["max"] == 5
    assert F.BANDS["q7"]["max"] == 5
    assert F.BANDS["q8"]["max"] == 6
    assert F.RAW_MAX == 21


def test_har_ballda_izoh_bor():
    for blk, meta in F.BANDS.items():
        for p in range(meta["max"] + 1):
            lab, why = F.band_label(blk, p)
            assert lab and len(why) > 15, (blk, p)


# =================================================================
#  2. BALL — Jahongir bergan chegaralar
# =================================================================

def test_jahongir_chegaralari():
    kutilgan = [(75, "C1"), (70, "C1"), (65, "C1"),
                (64, "B2"), (57, "B2"), (51, "B2"),
                (50, "B1"), (40, "B1"), (30, "B1"),
                (29, "A2"), (15, "A2"), (14, "A1"), (0, "A1")]
    for score, want in kutilgan:
        got, _ = F.level_of(score)
        assert got == want, (score, got, want)


def test_shkala_chegaralari_uzluksiz():
    """Ikki daraja orasida bo'sh ball qolmasin."""
    seen = set()
    for lo, hi, _n, _d in F.LEVELS:
        for s in range(lo, hi + 1):
            assert s not in seen, s
            seen.add(s)
    assert seen == set(range(0, 76))


def test_xom_ball_75ga_ostmaydi_va_monoton():
    prev = -1
    for raw in range(0, F.RAW_MAX + 1):
        s = F.to_scale(raw)
        assert 0 <= s <= 75
        assert s >= prev, raw
        prev = s
    assert F.to_scale(F.RAW_MAX) == 75
    assert F.to_scale(0) == 0


def test_c1_uchun_deyarli_hamma_blok_kerak():
    """C1 (65+) arzon chiqmasligi kerak."""
    assert F.build_result({"q1_3": 4, "q4_6": 4, "q7": 4,
                           "q8": 4})["level"] == "B2"
    assert F.build_result({"q1_3": 5, "q4_6": 5, "q7": 5,
                           "q8": 4})["level"] == "C1"
    assert F.build_result({"q1_3": 3, "q4_6": 3, "q7": 3,
                           "q8": 2})["level"] == "B1"
    assert F.build_result({"q1_3": 2, "q4_6": 2, "q7": 1,
                           "q8": 1})["level"] == "A2"


def test_keyingi_daraja_masofasi():
    r = F.build_result({"q1_3": 4, "q4_6": 4, "q7": 4, "q8": 4})
    assert r["next_level"] == "C1"
    assert r["next_gap"] == 65 - r["score"]
    top = F.build_result({"q1_3": 5, "q4_6": 5, "q7": 5, "q8": 6})
    assert top["score"] == 75 and top["next_gap"] == 0


def test_ball_chegaradan_oshmaydi():
    r = F.build_result({"q1_3": 99, "q4_6": -5, "q7": 5, "q8": 99})
    assert r["blocks"][0]["point"] == 5
    assert r["blocks"][1]["point"] == 0
    assert r["blocks"][3]["point"] == 6
    assert r["score"] <= 75


# =================================================================
#  3. KONTENT
# =================================================================

def test_savollar_hajmi():
    assert len(S.P11) >= 30 and all(len(x["q"]) == 3 for x in S.P11)
    assert len(S.P12) >= 20 and all(len(x["q"]) == 3 for x in S.P12)
    assert len(S.P2) >= 20 and all(len(x["q"]) == 3 for x in S.P2)
    assert len(S.P3) >= 25


# Part 1.2 har doim shu savol bilan boshlanadi — bu takror emas,
# imtihon formatining o'zi (speaking_format.pdf, 3-bet).
_STANDART = "What do you see in these pictures?"


def test_savollar_takrorlanmagan():
    hammasi = [q for x in S.P11 for q in x["q"]]
    hammasi += [q for x in S.P12 for q in x["q"]]
    hammasi += [q for x in S.P2 for q in x["q"]]
    hammasi = [q for q in hammasi if q != _STANDART]
    dubl = sorted({q for q in hammasi if hammasi.count(q) > 1})
    assert not dubl, dubl


def test_p12_standart_savol_bilan_boshlanadi():
    for x in S.P12:
        assert x["q"][0] == _STANDART, x["topic"]


def test_p12_da_ikkita_rasm_tavsifi():
    for x in S.P12:
        assert len(x["a"].split()) >= 8, x["topic"]
        assert len(x["b"].split()) >= 8, x["topic"]
        assert x["a"] != x["b"]


def test_p3_har_tomonda_uchta_band():
    for x in S.P3:
        assert len(x["for"]) >= 3, x["topic"]
        assert len(x["against"]) >= 3, x["topic"]
        assert x["topic"].endswith("."), x["topic"]


def test_kitobdagi_namunalar_saqlangan():
    """PDF dagi rasmiy namunalar bazada bo'lishi kerak."""
    p11 = [q for x in S.P11 for q in x["q"]]
    assert "Please tell me about your best friend." in p11
    assert "Tell me about your country." in p11
    assert "What do you like to do in your free time?" in p11
    p12 = [q for x in S.P12 for q in x["q"]]
    assert "What are some advantages of walking over driving?" in p12
    p2 = [q for x in S.P2 for q in x["q"]]
    assert "Tell me about a critical decision you have made." in p2
    assert S.P3[0]["topic"].startswith("Citizens should be allowed")


# =================================================================
#  4. SHABLON VA NAMUNA
# =================================================================

def test_har_qismda_shablon_ibora_namuna():
    for k, g in G.GUIDE.items():
        assert len(g["template"]) >= 3, k
        assert sum(len(v) for v in g["phrases"].values()) >= 12, k
        assert g["sample"] and g["sample_q"], k
        assert len(g["notes"]) >= 3, k
        assert len(g["avoid"]) >= 3, k


def test_soz_meyori_vaqtdan_hisoblanadi():
    """Shablon va tahlilchi bir xil me'yordan foydalanishi kerak.

    2026-08-26 REGRESSIYA. Avval ikki xil raqam bor edi (45 soniya
    uchun 85-110 va 60-89) va namunaviy javob bir vaqtning o'zida
    "normal" ham, "juda uzun" ham deb baholanardi.
    """
    for k, g in G.GUIDE.items():
        assert g["words"] == G.target_words(g["seconds"]), k


def test_namunalar_yuqori_ball():
    """ENG MUHIM TEST — namuna o'z tahlilchisidan 4+ ball olsin."""
    blk = {"p11": "q1_3", "p12": "q4_6", "p2": "q7", "p3": "q8"}
    bad = []
    for k, g in G.GUIDE.items():
        kw = {}
        if k == "p3":
            kw = {"for_list": S.P3[0]["for"],
                  "against_list": S.P3[0]["against"]}
        a = G.analyse(g["sample"], g["seconds"], [g["sample_q"]], **kw)
        pt = G.estimate_point(blk[k], a)
        lo, hi = g["words"]
        if not (lo <= a["words"] <= hi) or pt < 4:
            bad.append((k, a["words"], (lo, hi), pt,
                        a["linker_count"], a["complex"]))
    assert not bad, bad


# =================================================================
#  5. TAHLILCHI
# =================================================================

def test_qisqa_javob_past_ball():
    a = G.analyse("I like my friend. He is good.", 30,
                  ["Please tell me about your best friend."])
    assert a["words"] < G.target_words(30)[0]
    assert G.estimate_point("q1_3", a) <= 2
    lab = {t["label"] for t in G.tips(a, "q1_3") if t["ok"] is False}
    assert "Nutq hajmi" in lab


def test_bir_tomonlama_uchinchi_qism_uch_ball():
    """Rasmiy mezon: faqat bitta ro'yxat = 3 ball (Lower B2).

    Matn ataylab YETARLI UZUNLIKDA — shunda ballni faqat MUVOZANAT
    yo'qligi tushiradi, qisqaligi emas.
    """
    t = S.P3[0]
    matn = (
        "I believe that citizens should be allowed to carry guns, and "
        "there are two reasons which I find particularly convincing. "
        "The first is that a weapon can help people protect themselves "
        "in situations where nobody else can. In a village where the "
        "nearest patrol is forty minutes away, a family that is "
        "attacked at night has no realistic alternative, and although "
        "we would all prefer to rely on the authorities, the "
        "authorities are simply not present at that moment. My second "
        "reason is that this also prevents people from becoming "
        "victims of crimes such as burglary. Research from several "
        "countries suggests that a thief who cannot know which house "
        "is armed will usually avoid the whole street, and therefore "
        "even families who own nothing benefit from their neighbours. "
        "For example, a friend of mine lives in a small town where "
        "almost every household keeps a rifle for hunting, and break-"
        "ins there are extremely rare compared with the city where I "
        "grew up. Furthermore, hunting itself is a tradition that has "
        "supported rural families for generations, and taking that "
        "away would damage a way of life that has existed far longer "
        "than the current debate. For all of these reasons I would "
        "argue that responsible adults who have passed a proper "
        "background check should keep this right, because the "
        "alternative leaves ordinary families defenceless.")
    a = G.analyse(matn, 120, [t["topic"]],
                  for_list=t["for"], against_list=t["against"])
    assert a["words"] >= G.target_words(120)[0] * 0.9, a["words"]
    assert a["balance"]["for"] >= 1
    assert a["balance"]["against"] == 0, a["balance"]
    assert G.estimate_point("q8", a) == 3
    lab = {x["label"] for x in G.tips(a, "q8") if x["ok"] is False}
    assert "Muvozanat" in lab


def test_muvozanatli_uchinchi_qism_tort_yoki_besh():
    t = S.P3[0]
    a = G.analyse(G.GUIDE["p3"]["sample"], 120, [t["topic"]],
                  for_list=t["for"], against_list=t["against"])
    assert a["balance"]["for"] >= 1 and a["balance"]["against"] >= 1
    assert G.estimate_point("q8", a) >= 4


def test_bosh_javob_nol():
    a = G.analyse("", 30, ["Tell me about your country."])
    assert G.estimate_point("q1_3", a) == 0
    assert G.tips(a, "q1_3")[0]["ok"] is False


def test_blok_talabi_darajaga_mos():
    """B1 bloki uchun murakkab tuzilma TALAB qilinmasligi kerak.

    2026-08-26 REGRESSIYA. Avval hamma blokka bir xil talab
    qo'yilgan edi va namunaviy B1 javobi 4 o'rniga 3 ball olardi.
    Rasmiy mezonda Higher B1 uchun "Simple grammatical structures
    are used correctly" deb yozilgan — murakkab tuzilma emas.
    """
    a = G.analyse(G.GUIDE["p12"]["sample"], 45,
                  [G.GUIDE["p12"]["sample_q"]])
    assert a["complex"] < 3
    assert G.estimate_point("q4_6", a) == 4
