# -*- coding: utf-8 -*-
"""CEFR WRITING — MASHQ QATLAMI (2026-08-26).

MUAMMO. "Esse yoz" deb qo'yish bilan yozuv o'smaydi: o'quvchi
yozadi, hech kim baholamaydi, xato takrorlanaveradi.

YECHIM. To'liq matnni avtomat baholab bo'lmaydi, lekin uning
MAYDA KO'NIKMALARINI baholash mumkin. Shu fayl aynan shularni
mashq qildiradi:

  w_register  Bu gap rasmiymi yoki norasmiy?
  w_close     Shu ochilishga qaysi yopilish mos keladi?
  w_formal    Norasmiy gapning rasmiy variantini tanlang
  w_phrase    Standart iborani to'ldiring (yoziladi)
  w_order     Abzatslarni to'g'ri tartibda joylang
  w_spot      To'rt gapdan qaysi biri uslubni buzyapti?
  w_missing   Uch banddan qaysi biri javobda YO'Q?

QOIDA — TEKSHIRILGAN MANBADAN GENERATSIYA. Oldingi to'plamlarda
qo'lda yozilgan mashqlarda o'nlab xato chiqqan edi (javob matnda
yo'q, ikkita to'g'ri variant va h.k.). Shuning uchun bu yerda
mashqlarning KO'PCHILIGI qo'lda emas, tekshirilgan manbadan
qurib olinadi:

  w_order   -> cefr_writing_guide.py dagi NAMUNA xatlar abzatsidan.
               To'g'ri tartib — namunaning o'z tartibi, xato
               bo'lishi MUMKIN EMAS.
  w_phrase  -> qo'llanmadagi ibora bankidan. Javob — o'sha
               iboradan olib tashlangan so'z, ya'ni har doim mavjud.
  w_spot    -> register ro'yxatidan: 3 ta rasmiy + 1 ta norasmiy.
               Toq gap qurilish bo'yicha aniq.
  w_formal  -> juftliklardan. Chalg'ituvchilar BOSHQA juftlikning
               rasmiy variantidan olinadi: register to'g'ri,
               ma'nosi xato — ya'ni ikkita to'g'ri javob chiqmaydi.

JAVOB O'RNI. Manba ro'yxatlarda to'g'ri javob birinchi turadi
(o'qish oson). Ekranda esa hammasi A da bo'lib qolmasligi uchun
deterministik aylantirish qo'llanadi.
"""
import hashlib as _h

from cefr_writing_guide import GUIDE

# ---------------------------------------------------------------
#  1. REGISTER — rasmiy / norasmiy gaplar
#     Bu ro'yxat w_register, w_spot va w_formal uchun ham manba.
# ---------------------------------------------------------------

FORMAL_SENT = [
    "I am writing to enquire about the course starting in September.",
    "I would be grateful if you could send me further details.",
    "Please accept my sincere apologies for the delay.",
    "I am writing to express my dissatisfaction with the service.",
    "I would like to draw your attention to a problem with my order.",
    "Should you require any further information, please let me know.",
    "I look forward to receiving your reply in due course.",
    "I am writing on behalf of the students of Group 4.",
    "I would therefore suggest that the meeting be postponed.",
    "Thank you for your time and consideration.",
    "I have attached my curriculum vitae for your consideration.",
    "I trust that you will look into this matter as soon as possible.",
    "I am writing with regard to the advertisement in yesterday's paper.",
    "Unfortunately, the item arrived in a damaged condition.",
    "I would appreciate it if you could arrange a replacement.",
    "It has come to my attention that the timetable has been changed.",
    "I regret to inform you that I shall be unable to attend.",
    "Please find enclosed a copy of the receipt.",
    "I wish to apply for the position advertised on your website.",
    "We would be honoured if you could join us on that occasion.",
]

INFORMAL_SENT = [
    "Hey, guess what? They're changing the timetable again!",
    "Sorry I'm late replying, things have been mad here.",
    "I can't make it on Friday, sorry about that.",
    "Let me know what you think, OK?",
    "It's a bit annoying, isn't it?",
    "Anyway, I'd better go now. Talk soon!",
    "Thanks a million for helping me out yesterday.",
    "Do you fancy coming along with me?",
    "I've got loads of homework this week.",
    "That new cafe is amazing, you should try it.",
    "Give me a shout if you need anything.",
    "I'm really excited about it, to be honest.",
    "We had a great time, it was such fun.",
    "Don't worry about it, honestly.",
    "Guess who I bumped into yesterday!",
    "I'll drop you a message when I get there.",
    "It was kind of weird, but nice.",
    "Loads of people turned up, way more than we expected.",
    "Hope you're doing OK these days.",
    "See you at the weekend then!",
]

# ---------------------------------------------------------------
#  2. NORASMIY -> RASMIY juftliklar (w_formal manbasi)
# ---------------------------------------------------------------

FORMAL_PAIRS = [
    ("I want to know about the course.",
     "I would like to enquire about the course."),
    ("Sorry for being late with this.",
     "Please accept my apologies for the delay."),
    ("Can you send me the details?",
     "I would be grateful if you could send me the details."),
    ("I'm writing because I'm angry about the service.",
     "I am writing to express my dissatisfaction with the service."),
    ("Tell me if you need anything else.",
     "Should you require any further information, please let me know."),
    ("Write back soon.",
     "I look forward to hearing from you."),
    ("I think you should move the meeting.",
     "I would suggest that the meeting be postponed."),
    ("Thanks for looking at this.",
     "Thank you for your time and consideration."),
    ("I've put my CV in here too.",
     "I have attached my CV for your consideration."),
    ("Please sort this out quickly.",
     "I trust you will look into this matter as soon as possible."),
    ("I saw your advert in the paper.",
     "I am writing with regard to your advertisement in the newspaper."),
    ("The thing arrived broken.",
     "Unfortunately, the item arrived in a damaged condition."),
    ("Can you swap it for a new one?",
     "I would appreciate it if you could arrange a replacement."),
    ("I heard the timetable changed.",
     "It has come to my attention that the timetable has been changed."),
    ("I can't come, sorry.",
     "I regret to inform you that I shall be unable to attend."),
    ("The receipt is in this envelope.",
     "Please find enclosed a copy of the receipt."),
    ("I want the job you advertised.",
     "I wish to apply for the position advertised on your website."),
    ("It would be great if you came.",
     "We would be honoured if you could join us."),
    ("I need more time for the essay.",
     "I would like to request an extension for the essay."),
    ("Your staff member was really helpful.",
     "I would like to commend one of your members of staff."),
    ("Give me my money back.",
     "I would therefore request a full refund."),
    ("This has happened before, you know.",
     "Regrettably, this is not the first time this has occurred."),
    ("I'm free any time next week.",
     "I would be available at any time convenient to you next week."),
    ("Let's meet on Tuesday instead.",
     "Would it be possible to reschedule the meeting for Tuesday?"),
    ("I'm sorry, it was my fault.",
     "I fully accept responsibility for the oversight."),
]

# ---------------------------------------------------------------
#  3. OCHILISH -> YOPILISH (w_close manbasi)
#     QOIDA: ism noma'lum -> faithfully; ism ma'lum -> sincerely;
#     do'st -> norasmiy yopilish.
# ---------------------------------------------------------------

OPEN_CLOSE = [
    ("Dear Sir or Madam,", "Yours faithfully,", "faithful",
     "Ism NOMA'LUM bo'lganda 'Yours faithfully' yoziladi. Buni "
     "eslab qolish oson: Sir/Madam va faithfully — ikkalasida ham "
     "ism yo'q."),
    ("Dear Sir,", "Yours faithfully,", "faithful",
     "Ism aytilmagan — demak faithfully."),
    ("Dear Madam,", "Yours faithfully,", "faithful",
     "Ism aytilmagan — demak faithfully."),
    ("Dear Mr Brown,", "Yours sincerely,", "sincere",
     "Ism MA'LUM bo'lganda 'Yours sincerely'. Ism bor -> sincerely."),
    ("Dear Ms Lee,", "Yours sincerely,", "sincere",
     "Familiya berilgan — sincerely."),
    ("Dear Dr Karimov,", "Yours sincerely,", "sincere",
     "Unvon va familiya bor — sincerely."),
    ("Dear Mrs Ahmedova,", "Yours sincerely,", "sincere",
     "Familiya bor — sincerely."),
    ("Dear Professor Hall,", "Yours sincerely,", "sincere",
     "Familiya bor — sincerely."),
    ("Dear Manager,", "Yours faithfully,", "faithful",
     "'Manager' — lavozim, ism emas. Shuning uchun faithfully."),
    ("Dear Editor,", "Yours faithfully,", "faithful",
     "Lavozim aytilgan, ism yo'q — faithfully."),
    ("Hi Aziz,", "Take care,", "informal",
     "Do'stga xat — norasmiy yopilish. 'Yours faithfully' bu yerda "
     "g'alati ko'rinadi."),
    ("Hey Nodira,", "See you soon,", "informal",
     "Norasmiy ochilish — norasmiy yopilish."),
    ("Hi there,", "Best,", "informal", "Norasmiy juftlik."),
    ("Hello Bek,", "Cheers,", "informal", "Norasmiy juftlik."),
    ("Hi Mum,", "Love,", "informal",
     "Oilaga xat — eng iliq yopilish."),
]

CLOSE_POOL = ["Yours faithfully,", "Yours sincerely,", "Take care,",
              "Best wishes,", "See you soon,", "Regards,"]

# ---------------------------------------------------------------
#  4. BAND QAMROVI (w_missing) — qo'lda, chunki mazmun kerak
# ---------------------------------------------------------------

MISSING = [
    {
        "task": "Write to the sports centre manager.",
        "bullets": ["explain why you are writing",
                    "describe the problem with the changing rooms",
                    "say what you would like the centre to do"],
        "draft": "I am writing regarding my membership at your sports "
                 "centre, which I have held for two years. Over the "
                 "past month the changing rooms have been left "
                 "unclean, and on two occasions there was no hot "
                 "water at all.",
        "gone": 2,
        "why": "Muammo va sabab bor, lekin NIMA QILINISHINI "
               "so'ramagan. Rasmiy xat talabsiz tugasa, javob "
               "berish qiyin bo'ladi.",
    },
    {
        "task": "Write to your college principal.",
        "bullets": ["say which club you want to start",
                    "explain why students need it",
                    "ask for a room and a weekly time"],
        "draft": "I am writing to propose the creation of a debating "
                 "club at our college. Many students have told me "
                 "they would like more chances to practise speaking "
                 "in public, and at present there is no such "
                 "opportunity. Could we be given the small hall on "
                 "Thursday afternoons?",
        "gone": -1,
        "why": "Uchala band ham qamrab olingan: klub nomi, sabab va "
               "xona so'rovi. Bunday holat ham bo'ladi — hushyor "
               "bo'ling.",
    },
    {
        "task": "Write to a hotel manager.",
        "bullets": ["give your booking details",
                    "describe what was wrong",
                    "say what you expect the hotel to do"],
        "draft": "The room I was given did not match the description "
                 "on your website: there was no balcony and the air "
                 "conditioning did not work. I would therefore "
                 "request a partial refund of the amount paid.",
        "gone": 0,
        "why": "Bron ma'lumoti (sana, raqam) yo'q. Usiz mehmonxona "
               "qaysi bron haqida ekanini topa olmaydi — shikoyat "
               "kuchsiz bo'ladi.",
    },
    {
        "task": "Write to a company about a volunteer position.",
        "bullets": ["say which position you are applying for",
                    "describe your relevant experience",
                    "say when you are available"],
        "draft": "I am writing to apply for the summer volunteer "
                 "position advertised on your website. Last year I "
                 "helped to run a reading club for fifteen children "
                 "aged seven to ten, where I prepared weekly "
                 "activities and learnt how to keep young readers "
                 "interested.",
        "gone": 2,
        "why": "Qachon bo'sh ekani aytilmagan. Ariza xatida bu "
               "amaliy ma'lumot — usiz suhbatga chaqirish qiyin.",
    },
    {
        "task": "Write to your neighbour's landlord.",
        "bullets": ["introduce yourself and where you live",
                    "explain the noise problem",
                    "suggest a solution"],
        "draft": "The music from flat 12 continues until two or three "
                 "in the morning, several nights a week. I have "
                 "spoken to the tenants twice, but nothing has "
                 "changed. Perhaps a written reminder about quiet "
                 "hours would help.",
        "gone": 0,
        "why": "Kim yozayotgani va qayerda turishi aytilmagan. "
               "Rasmiy xatda birinchi abzats shuning uchun kerak.",
    },
    {
        "task": "Write to a bookshop about a wrong order.",
        "bullets": ["say what you ordered and when",
                    "explain what arrived instead",
                    "ask for a solution"],
        "draft": "On 3rd April I ordered two copies of 'A Short "
                 "History of Time' from your online shop, order "
                 "number 4471. I would be grateful if you could send "
                 "the correct books and arrange collection of the "
                 "others.",
        "gone": 1,
        "why": "Nima kelgani aytilmagan — faqat buyurtma va talab "
               "bor. O'qigan odam nima xato bo'lganini bilmaydi.",
    },
    {
        "task": "Write to a language school.",
        "bullets": ["say which course you are interested in",
                    "ask about the price and the timetable",
                    "ask whether accommodation is available"],
        "draft": "I am writing to enquire about your four-week "
                 "intensive English course beginning in July. Could "
                 "you please tell me how much the course costs and "
                 "on which days the lessons take place?",
        "gone": 2,
        "why": "Turar joy haqidagi savol tushib qolgan. So'rov "
               "xatida har bir band ALOHIDA savol — birortasi "
               "qolib ketsa ball tushadi.",
    },
    {
        "task": "Write to thank a hospital department.",
        "bullets": ["say who you are thanking and why",
                    "describe what happened",
                    "suggest how the hospital could recognise them"],
        "draft": "I am writing to express my sincere thanks to Nurse "
                 "Ergasheva of Ward 6. When my mother was admitted "
                 "last month she was frightened and confused, and "
                 "Nurse Ergasheva stayed with her long after her "
                 "shift had ended.",
        "gone": 2,
        "why": "Taklif yo'q. Rahmat xati taklif bilan tugasa "
               "(\"mukofotlang\", \"rahmatimni yetkazing\") ancha "
               "kuchli chiqadi.",
    },
    {
        "task": "Write to apologise to a business partner.",
        "bullets": ["apologise for missing the meeting",
                    "explain briefly why",
                    "propose a new date"],
        "draft": "I am writing to apologise sincerely for my absence "
                 "from our meeting on Tuesday. I would be glad to "
                 "meet at any time that suits you next week, and I "
                 "have already prepared the figures we were due to "
                 "discuss.",
        "gone": 1,
        "why": "Sabab aytilmagan. Uzr xatida qisqa sabab bo'lishi "
               "kerak — bo'lmasa xat yuzaki tuyuladi.",
    },
    {
        "task": "Write to invite a speaker to your college.",
        "bullets": ["invite them and say what the event is",
                    "give the date, time and place",
                    "say why you have chosen them"],
        "draft": "On behalf of City College I am delighted to invite "
                 "you to our careers evening. As a graduate of this "
                 "college who now leads a design studio, your story "
                 "would mean a great deal to our students.",
        "gone": 1,
        "why": "Sana, soat va joy yo'q. Taklifnomada bu eng muhim "
               "ma'lumot — usiz taklif ishlamaydi.",
    },
    {
        "task": "Write to a travel company.",
        "bullets": ["say which trip you booked",
                    "explain what went wrong with the transport",
                    "say what compensation you expect"],
        "draft": "I booked your three-day mountain tour departing on "
                 "9th June, reference MT308. The minibus arrived two "
                 "hours late and broke down twice, so we missed the "
                 "guided walk that was included in the price.",
        "gone": 2,
        "why": "Qanday tovon kutayotgani aytilmagan. Shikoyat "
               "xatining oxirgi bandi doim ANIQ talab bo'lishi kerak.",
    },
    {
        "task": "Write to your manager about a training course.",
        "bullets": ["say which course you want to attend",
                    "explain how it will help your work",
                    "say how your duties will be covered"],
        "draft": "I would like to request permission to attend the "
                 "two-day project management course in Tashkent on "
                 "14-15 October. The training covers scheduling and "
                 "risk planning, which are exactly the areas where "
                 "our team has had difficulties this year.",
        "gone": 2,
        "why": "Ishingiz kim tomonidan qoplanishi aytilmagan. "
               "Rahbar aynan shuni so'raydi — oldindan javob bering.",
    },
]

# ---------------------------------------------------------------
#  QURISH
# ---------------------------------------------------------------


def _rot(opts, ci, salt):
    """To'g'ri javobni deterministik ravishda siljitadi.

    Manbada javob birinchi turadi. Aylantirmasak — ekranda hamma
    javob A bo'lib qoladi va o'quvchi mazmunni o'qimay qo'yadi.
    """
    n = len(opts)
    sh = int(_h.md5(salt.encode()).hexdigest(), 16) % n
    new = [None] * n
    for k, t in enumerate(opts):
        new[(k + sh) % n] = t
    return new, (ci + sh) % n


def _mk(kind, idx, prompt, opts, ci, explain, extra=None):
    d = {"kind": kind, "idx": idx, "prompt": prompt,
         "options": opts, "answer": ci, "explain": explain}
    if extra:
        d.update(extra)
    return d


def build_register():
    """Rasmiymi yoki norasmiy? — 40 ta."""
    out, i = [], 0
    pairs = ([(s, "Rasmiy") for s in FORMAL_SENT]
             + [(s, "Norasmiy") for s in INFORMAL_SENT])
    pairs.sort(key=lambda p: _h.md5(p[0].encode()).hexdigest())
    for sent, lab in pairs:
        opts = ["Rasmiy", "Norasmiy"]
        ci = opts.index(lab)
        ex = ("Rasmiy: qisqartma yo'q, to'liq shakllar va muloyim "
              "burilishlar ishlatilgan."
              if lab == "Rasmiy" else
              "Norasmiy: qisqartma (I'm, don't), so'zlashuv "
              "so'zlari yoki hissiy ohang bor.")
        out.append(_mk("w_register", i,
                       "Bu gap qaysi uslubda yozilgan?\n\n" + sent,
                       opts, ci, ex))
        i += 1
    return out


def build_close():
    """Ochilishga mos yopilish — 15 ta."""
    out = []
    for i, (op, cl, grp, why) in enumerate(OPEN_CLOSE):
        wrong = [c for c in CLOSE_POOL if c != cl]
        wrong.sort(key=lambda c: _h.md5((c + op).encode()).hexdigest())
        opts = [cl] + wrong[:2]
        opts, ci = _rot(opts, 0, "close%d" % i)
        out.append(_mk("w_close", i,
                       "Xat shunday boshlangan:\n\n" + op
                       + "\n\nQaysi yopilish mos keladi?",
                       opts, ci, why, {"group": grp}))
    return out


def build_formal():
    """Norasmiy gapning rasmiy variantini tanlash — 25 ta.

    Chalg'ituvchilar BOSHQA juftlikning rasmiy variantidan olinadi:
    uslub to'g'ri, ma'no xato. Shunda "ikkita ham to'g'ri" degan
    holat qurilish bo'yicha bo'lishi mumkin emas.
    """
    out = []
    for i, (inf, frm) in enumerate(FORMAL_PAIRS):
        others = [f for j, (_, f) in enumerate(FORMAL_PAIRS) if j != i]
        others.sort(key=lambda s: _h.md5((s + inf).encode()).hexdigest())
        opts = [frm] + others[:2]
        opts, ci = _rot(opts, 0, "formal%d" % i)
        out.append(_mk(
            "w_formal", i,
            "Rasmiy xatga mos variantni tanlang:\n\n«" + inf + "»",
            opts, ci,
            "Rasmiy uslubda qisqartma ishlatilmaydi va so'rov "
            "muloyim shaklga (would / could / I would like to) "
            "solinadi. Ma'no esa asl gap bilan bir xil qolishi kerak."))
    return out


def build_phrase():
    """Standart iborani to'ldirish — qo'llanma ibora bankidan.

    Javob har doim iboraning O'ZIDAN olinadi, shuning uchun
    "javob matnda yo'q" degan xato bo'lishi mumkin emas.
    """
    skip = {"i", "a", "an", "the", "to", "of", "for", "and", "in",
            "on", "at", "you", "your", "my", "me", "we", "us", "is",
            "am", "are", "be", "it", "that", "this", "if", "with",
            "would", "could", "will", "can", "do", "have", "has"}
    out, i = [], 0
    seen = set()
    for g in GUIDE:
        for st in g["steps"]:
            for ph in st["phrases"]:
                if "..." in ph or len(ph.split()) < 4:
                    continue
                if ph in seen:
                    continue
                seen.add(ph)
                words = ph.split()
                cands = [(k, w) for k, w in enumerate(words)
                         if w.strip(".,!?").lower() not in skip
                         and w.strip(".,!?").isalpha()
                         and len(w.strip(".,!?")) > 3]
                if not cands:
                    continue
                # 2026-08-26 TUZATISH. Savol sarlavhasida xat turi
                # yozilgani uchun ("Thank-you letter"), javob "thank"
                # bo'lsa — javob savolning O'ZIDA turib qolardi.
                # Test shu tuzoqni tutdi. Endi sarlavha va qadam
                # nomida uchraydigan so'zlar javob bo'la olmaydi.
                head = (g["title"] + " " + st["name"]).lower()
                safe = [(k, w) for k, w in cands
                        if w.strip(".,!?").lower() not in head]
                use = safe or cands
                pick = int(_h.md5(ph.encode()).hexdigest(), 16) % len(use)
                k, w = use[pick]
                ans = w.strip(".,!?")
                if ans.lower() in head:
                    continue
                tail = w[len(ans):]
                blanked = words[:k] + ["………" + tail] + words[k + 1:]
                out.append({
                    "kind": "w_phrase", "idx": i,
                    "prompt": ("Iborani to'ldiring — " + g["title"]
                               + " (" + st["name"] + "):\n\n"
                               + " ".join(blanked)),
                    "answer": ans,
                    "explain": "To'liq ibora: " + ph,
                    "type": g["key"],
                })
                i += 1
    return out


def build_order():
    """Abzatslarni tartibga solish — namuna xatlardan.

    To'g'ri tartib namunaning o'z tartibi. Qo'lda yozilmagani
    uchun bu yerda mazmun xatosi bo'lishi mumkin emas.
    """
    out = []
    for i, g in enumerate(GUIDE):
        paras = g["model"]["paras"]
        pieces = []
        for role, text, _why in paras:
            first = text.replace("\n", " ").strip()
            if len(first) > 150:
                first = first[:147].rsplit(" ", 1)[0] + "…"
            pieces.append({"role": role, "text": first})
        order = list(range(len(pieces)))
        sh = sorted(order, key=lambda k: _h.md5(
            (g["key"] + str(k)).encode()).hexdigest())
        out.append({
            "kind": "w_order", "idx": i,
            "prompt": (g["title"] + " — abzatslarni to'g'ri "
                       "tartibda bosing."),
            "pieces": [pieces[k] for k in sh],
            "answer": [sh.index(k) for k in order],
            "explain": "To'g'ri tartib: "
                       + " -> ".join(p["role"] for p in pieces),
            "type": g["key"],
        })
    return out


def build_spot():
    """Uslubni buzayotgan gapni topish — 20 ta.

    3 ta rasmiy + 1 ta norasmiy (yoki teskarisi). Toq gap
    qurilish bo'yicha aniq — ikkilanish bo'lmaydi.
    """
    out = []
    for i in range(20):
        formal_ctx = i % 2 == 0
        base = FORMAL_SENT if formal_ctx else INFORMAL_SENT
        odd = INFORMAL_SENT if formal_ctx else FORMAL_SENT
        b = [base[(i * 3 + k) % len(base)] for k in range(3)]
        o = odd[(i * 5) % len(odd)]
        opts = [o] + b
        opts, ci = _rot(opts, 0, "spot%d" % i)
        ctx = ("RASMIY xatdan olingan gaplar."
               if formal_ctx else "DO'STGA yozilgan xatdan olingan gaplar.")
        why = ("Rasmiy xatda qisqartma va so'zlashuv iboralari "
               "ishlatilmaydi — shu gap uslubni buzyapti."
               if formal_ctx else
               "Do'stga yozilgan xatda rasmiy burilishlar g'alati "
               "ko'rinadi — shu gap uslubni buzyapti.")
        out.append(_mk("w_spot", i,
                       ctx + "\nQaysi biri uslubga MOS EMAS?",
                       opts, ci, why))
    return out


def build_missing():
    """Qaysi band javobda yo'q — 12 ta."""
    out = []
    for i, m in enumerate(MISSING):
        opts = list(m["bullets"]) + ["Hammasi qamrab olingan"]
        ci = len(m["bullets"]) if m["gone"] < 0 else m["gone"]
        out.append(_mk(
            "w_missing", i,
            m["task"] + "\n\nTopshiriq bandlari yuqorida. "
            "Quyidagi javobda qaysi band YO'Q?\n\n«"
            + m["draft"] + "»",
            opts, ci, m["why"]))
    return out


BUILDERS = {
    "w_register": build_register,
    "w_close": build_close,
    "w_formal": build_formal,
    "w_phrase": build_phrase,
    "w_order": build_order,
    "w_spot": build_spot,
    "w_missing": build_missing,
}

DRILL_META = [
    {"kind": "w_register", "title": "Rasmiy yoki norasmiy?",
     "desc": "Gapni o'qib uslubini aniqlang. Bu — 1.1 va 1.2 ni "
             "adashtirmaslikning asosi."},
    {"kind": "w_formal", "title": "Rasmiy shaklga o'tkazish",
     "desc": "Kundalik gapni rasmiy xat tiliga aylantiring."},
    {"kind": "w_close", "title": "Ochilish va yopilish",
     "desc": "Dear Sir or Madam -> Yours faithfully. Bu juftlikni "
             "adashtirish — eng ko'p uchraydigan xato."},
    {"kind": "w_phrase", "title": "Iborani to'ldiring",
     "desc": "Standart iboralarni yoddan yozib mustahkamlang."},
    {"kind": "w_order", "title": "Abzatslar tartibi",
     "desc": "Namuna xatning abzatslarini to'g'ri joyiga qo'ying."},
    {"kind": "w_spot", "title": "Uslubni buzgan gapni toping",
     "desc": "To'rt gapdan bittasi uslubga mos emas."},
    {"kind": "w_missing", "title": "Qaysi band tushib qolgan?",
     "desc": "Bandni qoldirib ketish — ball yo'qotishning eng "
             "achinarli sababi."},
]

_CACHE: dict[str, list] = {}


def items(kind: str) -> list:
    if kind not in _CACHE:
        b = BUILDERS.get(kind)
        _CACHE[kind] = b() if b else []
    return _CACHE[kind]


def counts() -> dict:
    return {k: len(items(k)) for k in BUILDERS}
