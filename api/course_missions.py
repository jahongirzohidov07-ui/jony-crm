"""Curriculum-grounded creative tasks and observable hints, never a skill grader."""
import re
import unicodedata


def _normal(text):
    return unicodedata.normalize("NFC", text).casefold().replace("’", "'")


def _targets(row):
    # Use actual grammar answers, not inferred CEFR requirements or reading names.
    words = []
    for section in row["sections"]:
        if section["skill"] != "grammar":
            continue
        for question in section["questions"]:
            if question["mode"] != "exact":
                continue
            for answer in question.get("expected", []):
                if re.fullmatch(r"[^\W\d_][^\W\d_'-]{1,19}", answer, re.UNICODE):
                    if _normal(answer) not in {_normal(w) for w in words}:
                        words.append(answer)
    return words[:6]


def choices(language, row):
    """Each ID is scoped to a validated language/lesson; all choices are optional."""
    lesson = row["lesson"]
    targets = _targets(row)
    context = _normal(row["title"] + " " + " ".join(
        q.get("explanation", "") for s in row["sections"] if s["skill"] == "grammar"
        for q in s["questions"]))
    foundation = (language == "en" and lesson <= 6) or (language == "de" and lesson == 1)
    if foundation:
        specs = [
            ("identity-card", "Tanishuv kartam", "Yangi tanishingiz uchun o‘zingiz tanlagan ism va darsdagi so‘zlardan kichik karta yarating. To‘liq gap shart emas.", "story"),
            ("object-label", "Men tanlagan buyum", "Do‘stingizga ko‘rsatmoqchi bo‘lgan buyum yoki qahramonga darsdagi so‘zlar bilan yorliq yozing. Alohida so‘zlar yetarli.", "story"),
        ]
    else:
        specs = []
        if (language == "en" and re.search(r"\b(am|is|are|to be)\b", context)) or (language == "de" and ("tanishuv" in context or lesson == 2)):
            specs.append(("introduce", "Yangi tanishga o‘zimni tanishtiraman", "Kursdagi yangi tanishingizga o‘zingiz yoki o‘ylab topgan qahramoningiz haqida dars qoliplari bilan qisqa tanishuv yozing.", "dialogue"))
        if (language == "en" and re.search(r"\b(can|could|may|request)\b", context)) or (language == "de" and re.search(r"\b(können|könnt|kann|bitte|yordam)\b", context)):
            specs.append(("request-help", "Yordam so‘rayman", "Darsda yoki kundalik ishda kerak bo‘lgan bitta yordamni tanlang. Darsdagi qolip bilan sherigingizdan so‘rang va uning javobini yozing.", "dialogue"))
        if (language == "en" and re.search(r"\b(past|was|were)\b", context)) or (language == "de" and re.search(r"\b(perfekt|präteritum|kechagi|war|waren)\b", context)):
            specs.append(("past-event", "Bo‘lgan voqeani aytaman", "Do‘stingizga kecha yoki avval bo‘lgan kichik voqeani aytib bering. Haqiqiy yoki o‘ylab topilgan voqeani darsdagi o‘tgan zamon qolipi bilan yozing.", "story"))
        if (language == "en" and re.search(r"\b(because|opinion|comparative|although)\b", context)) or (language == "de" and re.search(r"\b(weil|denn|meinung|obwohl)\b", context)):
            specs.append(("justify-choice", "Tanlovimni tushuntiraman", "Do‘stingiz bilan joy, mashg‘ulot yoki buyum tanlang. O‘z tanlovingizni va bitta sababini shu darsdagi vositalar bilan yozing.", "story"))
        # These tasks stay at the current lesson's forms; they require no new tense.
        specs.extend([
            ("friend-message", "Do‘stimga kichik xabar", "Bugun sizga muhim bo‘lgan bir narsa haqida do‘stingizga xabar yozing. Shu darsdagi so‘z va qoliplardan foydalaning; vaziyatni o‘zingiz tanlang.", "story"),
            ("shared-scene", "Birgalikdagi vaziyat", "Do‘stingiz bilan maktab, uy yoki sevimli mashg‘ulotdagi vaziyatni tanlang. Darsdagi so‘z va qoliplar bilan navbatma-navbat ikki qisqa replika yozing.", "dialogue"),
        ])
    return [{"id": f"{language}:{lesson}:{key}", "title": title, "prompt": prompt,
             "suggested_type": kind, "targets": targets, "foundation": foundation,
             "lesson_title": row["title"], "language": language, "lesson": lesson}
            for key, title, prompt, kind in specs[:4]]


def coaching(row, version, mission=None):
    text = version["text"].strip()
    foundation = ((row.get("language") == "en" and row["lesson"] <= 6)
                  or (row.get("language") == "de" and row["lesson"] == 1))
    targets = mission["targets"] if mission else _targets(row)
    foundation = mission["foundation"] if mission else foundation
    disclaimer = "Bu matndagi belgilar bo‘yicha maslahat; grammatik to‘g‘rilik yoki til darajasi bahosi emas. Audio mazmuni va talaffuzi tekshirilmagan."
    final_version = version.get("number", 1) >= 3
    retry = ("Shu bitta qadamni alohida yangi ishda bajaring. Uchta saqlangan versiyangiz o‘zgarishsiz qoladi."
             if final_version else "Shu bitta qadamni bajaring va yangi versiyani saqlab, oldingisi bilan solishtiring.")
    if not text:
        return {"observed_positive": "Ovozli yozuvingiz ushbu versiyaga biriktirilgan.",
                "next_improvement": "Yozuvda aytmoqchi bo‘lgan bitta asosiy iborani matn maydoniga ham yozing.",
                "retry": retry,
                "basis": "audio_unassessed", "disclaimer": disclaimer,
                "verified_mastery": False, "assessed_audio": False}
    matched = [w for w in targets if re.search(r"(?<!\w)" + re.escape(_normal(w)) + r"(?!\w)", _normal(text))]
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if matched:
        positive = f"Matningizda darsdan «{matched[0]}» so‘zi bor."
    elif version["type"] == "dialogue" and len(lines) >= 2:
        positive = "Dialog matni kamida ikki alohida satrga ajratilgan."
    else:
        positive = "O‘z matningizni yozdingiz; uni qayta ishlab davom ettirish mumkin."
    if targets and not matched:
        improvement = f"Darsdagi «{targets[0]}» so‘zini vaziyatingizga mos bitta iborada ishlatib ko‘ring."
    elif foundation:
        improvement = "Tanlagan buyum yoki qahramoningizga darsdan yana bitta mos so‘z qo‘shing; to‘liq gap shart emas."
    elif version["type"] == "dialogue" and len(lines) < 2:
        improvement = "Sherigingizning bitta javobini yangi satrga yozib, suhbatni davom ettiring."
    elif text[-1:] not in ".!?…":
        improvement = "Oxirgi fikringiz tugagan joyga mos nuqta yoki so‘roq belgisini qo‘ying."
    else:
        improvement = "Vaziyatni aniqroq qilish uchun bitta joy yoki buyum tafsilotini darsdagi qolip bilan qo‘shing."
    return {"observed_positive": positive, "next_improvement": improvement,
            "retry": retry,
            "basis": "text_patterns", "disclaimer": disclaimer,
            "verified_mastery": False, "assessed_audio": False}
