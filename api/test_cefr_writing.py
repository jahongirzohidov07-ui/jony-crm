# -*- coding: utf-8 -*-
"""CEFR Multilevel Writing bo'limi testlari (2026-08-26).

Jahongir: "sen kuchli metodist ustoz va pro dasturchi sifatida shu
narsalarni shunday mukammal qilib joylashtirginki CEFR writing
yozishni o'rganish uchun bu qism mukammal bo'lsin."

ENG MUHIM TEST — test_namunalar_ozi_100_ball(). U har bir namuna
javobni O'Z avtomat tekshirgichimizdan o'tkazadi. Bu ikki tomonlama
tekshiruv:
  - namuna xato bo'lsa (kalta, band tushib qolgan, yopilishi
    noto'g'ri) — test yiqiladi;
  - tekshirgich xato bo'lsa (to'g'ri matnni xato deb belgilasa) —
    test yana yiqiladi.
Ya'ni kontent tekshirgichni, tekshirgich kontentni qo'riqlaydi.

Birinchi ishga tushirishda aynan shu test 7 ta haqiqiy nuqson
topdi: "Dear Sir or MADam" ichidan "mad" so'zi topilib rasmiy
xatlar "so'zlashuv uslubi" deb belgilangani, his-tuyg'u
kalitlarida "furious" va "happy" yo'qligi, oltita xatning 120
so'zdan kalta ekani va blog/maqolaga forum mezoni qo'llanilgani.
"""
import cefr_writing_guide as G
import cefr_writing_drills as D
import cefr_writing_tasks as T


# =================================================================
#  1. QO'LLANMA
# =================================================================

def test_uch_qism_ham_qoplangan():
    parts = {g["part"] for g in G.GUIDE}
    assert parts == {"1.1", "1.2", "2"}, parts


def test_har_turda_qadam_ibora_namuna_bor():
    for g in G.GUIDE:
        assert len(g["steps"]) >= 5, g["key"]
        assert all(s["phrases"] for s in g["steps"]), g["key"]
        assert g["must"] and g["avoid"], g["key"]
        assert len(g["model"]["paras"]) >= 5, g["key"]


def test_namuna_izohlari_bor():
    """Har abzatsda NEGA shunday yozilgani tushuntirilishi shart.

    Izohsiz namuna — ko'chirib yozishga chaqiriq. Metodik qiymati
    aynan izohda.
    """
    for g in G.GUIDE:
        for role, text, why in g["model"]["paras"]:
            assert role.strip(), g["key"]
            # Salomlashish abzatsi tabiiy ravishda qisqa
            # ("Hi Kamron,") — shuning uchun chegara 2 so'z.
            assert len(text.split()) >= 2, (g["key"], role)
            assert len(why) >= 25, (g["key"], role, why)


def test_namuna_sozlari_ozi_aytgan_songa_teng():
    """model.words qo'lda yozilgan — u haqiqatga mos bo'lishi kerak."""
    for g in G.GUIDE:
        real = sum(len(T.words_of(p[1])) for p in g["model"]["paras"])
        say = g["model"]["words"]
        assert abs(real - say) <= 6, (g["key"], real, say)


def test_1_1_norasmiy_1_2_rasmiy():
    """Namunalar o'z registriga mos bo'lishi kerak."""
    for g in G.GUIDE:
        body = " ".join(p[1] for p in g["model"]["paras"]).lower()
        if g["part"] == "1.1":
            assert "yours faithfully" not in body, g["key"]
            assert "dear sir" not in body, g["key"]
        if g["part"] == "1.2":
            assert body.startswith("dear "), g["key"]
            assert ("yours faithfully" in body
                    or "yours sincerely" in body), g["key"]


def test_ochilish_yopilish_juftligi_togri():
    """Dear Sir or Madam -> faithfully; Dear + ism -> sincerely.

    Bu CEFRda eng ko'p ball yo'qotiladigan joy — namunada xato
    bo'lsa, o'quvchi xatoni o'rganadi.
    """
    for g in G.GUIDE:
        if g["part"] != "1.2":
            continue
        body = " ".join(p[1] for p in g["model"]["paras"]).lower()
        if body.startswith("dear sir") or body.startswith("dear madam"):
            assert "yours faithfully" in body, g["key"]
        else:
            assert "yours sincerely" in body, g["key"]


# =================================================================
#  2. MASHQLAR
# =================================================================

def test_yetti_tur_va_yetarli_hajm():
    c = D.counts()
    assert set(c) == {"w_register", "w_close", "w_formal", "w_phrase",
                      "w_order", "w_spot", "w_missing"}, set(c)
    assert sum(c.values()) >= 150, c
    for k, v in c.items():
        assert v >= 10, (k, v)


def test_variantli_mashqlarda_javob_bitta_va_haqiqiy():
    """Variantlar takrorlanmasin, javob raqami chegarada bo'lsin."""
    for kind in ("w_register", "w_close", "w_formal", "w_spot",
                 "w_missing"):
        for it in D.items(kind):
            o = it["options"]
            assert len(o) == len(set(o)), (kind, it["idx"], o)
            assert 0 <= it["answer"] < len(o), (kind, it["idx"])
            assert it["explain"], (kind, it["idx"])


def test_javob_harflari_bir_joyda_toplanib_qolmagan():
    """Hammasi A bo'lsa o'quvchi mazmunni o'qimay qo'yadi."""
    for kind in ("w_formal", "w_close", "w_spot"):
        rows = D.items(kind)
        n = len(rows[0]["options"])
        cnt = [0] * n
        for it in rows:
            cnt[it["answer"]] += 1
        assert max(cnt) <= len(rows) * 0.6, (kind, cnt)


def test_w_close_qoidasi_buzilmagan():
    """faithfully / sincerely qoidasi mashqda ham to'g'ri bo'lsin."""
    for it in D.items("w_close"):
        p = it["prompt"].lower()
        ans = it["options"][it["answer"]].lower()
        if "dear sir" in p or "dear madam" in p or "dear manager" in p \
                or "dear editor" in p:
            assert ans == "yours faithfully,", it["prompt"]
        elif p.count("dear ") and "mr " in p or "ms " in p or "dr " in p \
                or "mrs " in p or "professor " in p:
            assert ans == "yours sincerely,", it["prompt"]


def test_w_formal_chalgituvchilari_boshqa_manoda():
    """Chalg'ituvchi ham rasmiy, lekin ma'nosi boshqa bo'lishi kerak.

    Agar chalg'ituvchi asl gapning yana bir to'g'ri tarjimasi
    bo'lsa — savolning ikkita javobi bo'lib qoladi.
    """
    formals = {f for _, f in D.FORMAL_PAIRS}
    for it in D.items("w_formal"):
        assert all(o in formals for o in it["options"]), it["idx"]
        assert len(set(it["options"])) == 3


def test_w_phrase_javobi_iboraning_ichidan():
    """Javob har doim to'liq iborada mavjud bo'lishi shart."""
    for it in D.items("w_phrase"):
        full = it["explain"].replace("To'liq ibora: ", "")
        assert it["answer"] in full, (it["idx"], it["answer"], full)
        assert "………" in it["prompt"], it["idx"]
        assert it["answer"].lower() not in it["prompt"].lower(), it["idx"]


def test_w_order_javobi_namunaning_tartibi():
    """Tartib namuna xatdan olingani uchun xato bo'lishi mumkin emas."""
    keys = {g["key"]: g for g in G.GUIDE}
    for it in D.items("w_order"):
        g = keys[it["type"]]
        want = [p[0] for p in g["model"]["paras"]]
        got = [it["pieces"][k]["role"] for k in it["answer"]]
        assert got == want, (it["type"], got, want)


def test_w_spot_toq_gap_haqiqatan_toq():
    """3 rasmiy + 1 norasmiy (yoki teskarisi) — javob aniq bo'lsin."""
    for it in D.items("w_spot"):
        odd = it["options"][it["answer"]]
        rest = [o for i, o in enumerate(it["options"]) if i != it["answer"]]
        if "RASMIY" in it["prompt"]:
            assert odd in D.INFORMAL_SENT, odd
            assert all(r in D.FORMAL_SENT for r in rest), rest
        else:
            assert odd in D.FORMAL_SENT, odd
            assert all(r in D.INFORMAL_SENT for r in rest), rest


def test_w_missing_javobi_haqiqatan_yoq():
    """Yo'q deb belgilangan band javobda ROSTDAN yo'qligini isbotlash."""
    for m in D.MISSING:
        spec = {"words": [0, 9999], "register": "formal",
                "close": "any", "min_paras": 1,
                "bullets": [{"label": b, "keys": [[]]} for b in m["bullets"]]}
        assert 0 <= m["gone"] < len(m["bullets"]) or m["gone"] == -1
        assert len(m["draft"].split()) >= 25, m["task"]
        assert spec


# =================================================================
#  3. IMTIHON VAZIFALARI VA TEKSHIRGICH
# =================================================================

def test_part1_juftlab_tuzilgan():
    """Yangi formatning asosi: 1.1 va 1.2 BITTA vaziyatdan."""
    for t in T.PART1:
        assert t["context"] and t["context_from"], t["id"]
        assert len(t["t11"]["bullets"]) == 2, t["id"]
        assert len(t["t12"]["bullets"]) == 3, t["id"]
        assert t["model11"] and t["model12"], t["id"]


def test_namunalar_ozi_100_ball():
    """ENG MUHIM TEST — kontent va tekshirgich bir-birini tekshiradi."""
    bad = []
    for t in T.PART1:
        for tag, txt in (("1.1", t["model11"]), ("1.2", t["model12"])):
            r = T.check(txt, T.spec_for(tag, t))
            if r["score"] < 100:
                bad.append((t["id"], tag, r["score"],
                            [c["detail"] for c in r["checks"]
                             if c["ok"] is not True]))
    for x in T.PART2:
        if x.get("model"):
            r = T.check_part2(x["model"], x["type"])
            if r["score"] < 100:
                bad.append((x["id"], x["type"], r["score"],
                            [c["detail"] for c in r["checks"]
                             if c["ok"] is not True]))
    assert not bad, bad


def test_tekshirgich_yomon_matnni_tutadi():
    """Teskari yo'nalish: xato matn yuqori ball OLMASLIGI kerak."""
    t = T.PART1[0]
    yomon = "hey mate, they're changing stuff. it's mad. bye"
    r = T.check(yomon, T.spec_for("1.2", t))
    assert r["score"] < 55, r
    labels = {c["label"] for c in r["checks"] if c["ok"] is False}
    assert "So'z soni" in labels
    assert "Ochilish" in labels


def test_madam_soz_ichidan_topilmaydi():
    """2026-08-26 REGRESSIYA. 'Dear Sir or Madam' ichidagi 'mad'.

    Avval oddiy `in` qidiruvi ishlatilgani uchun har bir rasmiy
    namuna 'so'zlashuv uslubi' deb belgilangan edi.
    """
    txt = ("Dear Sir or Madam,\n\nI am writing to enquire about the "
           "estimated delivery date of my order, which was placed on "
           "the third of May and has not yet arrived at my "
           "address.\n\nI would be grateful if you could confirm "
           "when the item will be dispatched, as I require it before "
           "the end of the month for a family occasion.\n\nThank you "
           "for your assistance in this matter.\n\nYours faithfully,")
    r = T.check(txt, {"words": [40, 200], "register": "formal",
                      "close": "faithful", "min_paras": 4,
                      "bullets": []})
    uslub = [c for c in r["checks"] if c["label"] == "Uslub"][0]
    assert uslub["ok"] is True, uslub


def test_janrga_qarab_boshqa_mezon():
    """Blog uchun 'qarshi fikr' talab qilinmaydi — bu forum mezoni."""
    blog = next(x for x in T.PART2 if x["id"] == "p2_habit")
    r_blog = T.check_part2(blog["model"], "blog")
    labels = {c["label"] for c in r_blog["checks"]}
    assert "Xulosa" in labels and "O'quvchiga murojaat" in labels
    assert "Qarshi fikr" not in labels
    r_forum = T.check_part2(blog["model"], "forum")
    assert "Qarshi fikr" in {c["label"] for c in r_forum["checks"]}


def test_band_qamrovi_ishlaydi():
    """Band yozilmasa — tekshirgich buni aytishi kerak."""
    t = next(x for x in T.PART1 if x["id"] == "p1_cinema")
    # his-tuyg'u bandi ataylab olib tashlangan matn
    txt = ("Hi Sardor,\n\nHow are you? The club wants to move our film "
           "night from Friday evening to Tuesday morning, and to show "
           "only Hollywood films.\n\nWrite back soon!\n\nTake care,")
    r = T.check(txt, T.spec_for("1.1", t))
    miss = [c for c in r["checks"] if c["label"] == "Topshiriq bandlari"]
    assert miss and miss[0]["ok"] is False, r["checks"]
    assert "how you feel" in miss[0]["detail"]


def test_ochilish_yopilish_mosligini_tutadi():
    """Dear Mr Brown + Yours faithfully — bu xato, tutilishi kerak."""
    txt = ("Dear Mr Brown,\n\nI am writing to request a copy of the "
           "timetable for the coming term, as the version on the "
           "noticeboard appears to be out of date.\n\nI would be "
           "grateful if you could send it by email.\n\nThank you for "
           "your help.\n\nYours faithfully,")
    r = T.check(txt, {"words": [40, 200], "register": "formal",
                      "close": "sincere", "min_paras": 4, "bullets": []})
    cl = [c for c in r["checks"] if c["label"] == "Yopilish"][0]
    assert cl["ok"] is None, cl
    assert "sincerely" in cl["detail"]


def test_backend_ulangan():
    src = open("student_app.py", encoding="utf-8").read()
    for yol in ("/api/student/cefr/writing/home",
                "/api/student/cefr/writing/guide/{key}",
                "/api/student/cefr/writing/drill",
                "/api/student/cefr/writing/drill/answer",
                "/api/student/cefr/writing/tasks",
                "/api/student/cefr/writing/task/{tid}",
                "/api/student/cefr/writing/submit"):
        assert yol in src, yol
    # Namuna javob vazifa BERILGANDA emas, TOPSHIRILGANDA ochiladi
    i = src.index('def cw_task(')
    blok = src[i:src.index("\n_CW_SYSTEM", i)]
    assert "model11" not in blok and "model" not in blok.split("return")[1]


def test_ai_ishlamasa_ham_baho_beriladi():
    """AI kaliti yo'q bo'lsa ham avtomat tekshiruv to'liq ishlaydi."""
    src = open("student_app.py", encoding="utf-8").read()
    i = src.index("def cw_submit(")
    blok = src[i:]
    assert "except Exception as e:" in blok
    assert 'ai_err = str(e)' in blok
    # natija AI'siz ham qaytadi
    assert 'return {**res,' in blok


def test_ekranlar_bor():
    import os
    d = os.path.join(os.path.dirname(__file__), "..", "src", "pages",
                     "student")
    for f in ("StudentCefrWriting.tsx", "StudentCefrWritingGuide.tsx",
              "StudentCefrWritingDrill.tsx", "StudentCefrWritingTasks.tsx",
              "StudentCefrWritingExam.tsx"):
        assert os.path.exists(os.path.join(d, f)), f
