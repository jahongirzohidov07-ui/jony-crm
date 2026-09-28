# -*- coding: utf-8 -*-
"""WRITING AI BAHOSI (2026-09-28).

Jahongir: "Writingni ham avtobaholaydigan qilib qoysak yaxshi bo'lardi.
Hech qanday muammolarsiz bo'lishi yaxshi bolardi".

Mock Writing insholarini AI examiner baholaydi, yakuniy ballni esa
mavjud kalkulyator (mock_marking) chiqaradi — AI va examiner bir xil
arifmetikadan foydalanadi:

  IELTS  har topshiriq 4 mezon (Task Achievement/Response, Coherence
         and Cohesion, Lexical Resource, Grammatical Range and
         Accuracy), har biri butun band 0-9. Task 2 ikki barobar
         og'ir: mezon = (T1 + 2*T2) / 3, keyin mock_marking.ielts_band —
         o'rtacha BIR marta IELTS qoidasi bilan yaxlitlanadi.
  CEFR   yangi 3 topshiriqli format (2025-10-13 yakuniy shkala): 1.1 va
         1.2 -> 0-5, Part 2 -> 0-6, keyin mock_marking.cefr_writing_new
         rasmiy konversiya jadvali bo'yicha -> 0-75 va daraja.

Kalibrovka (2026-09-28, Jahongir: "internetdan real examinerlarning
sample writinglarga bergan sample feedbacklarini topib shulardan organib
shunaqa baho qoyish kerak"): promptlarda rasmiy IELTS band descriptors
(May 2023) va Multilevel yakuniy shkalasining band chegaralari (5/6,
6/7, 7/8), jarima qoidalari va rasmiy examiner comment tartibi —
hammasi o'z so'zlarimiz bilan qayta yozilgan. Multilevel shkaladagi
hajm chegaralari (masalan, 1.2 da 60 so'zgacha — ko'pi bilan 2) kodda
ham qo'llanadi (CEFR_LENGTH_CAPS).

Qoidalar:
  - Bo'sh insho AI'ga yuborilmaydi va 0 oladi; IELTS'da 1-20 so'zli
    javob — rasmiy qoida bo'yicha Band 1 (AI'siz). Hammasi shunday
    bo'lsa AI umuman chaqirilmaydi.
  - Topshiriqlar AI'ga "T1/T2/T3" identifikatori bilan boradi — javob
    shu bo'yicha bog'lanadi ("Task 2" va 2-savol chalkashmaydi).
  - Izoh INGLIZCHA, rasmiy examiner comment uslubida (Jahongir: "writing
    feedback inglizcha bolishi kerak men senga sample feedbacklar papkaga
    qoshib qoydim"): IELTS — bitta paragraf, 4 mezon tartibida, matndan
    qavs ichida dalil va yuqoriroq band uchun nima kerakligi
    ("ielts-academic-writing-example-responses-...-examiner-comments.pdf");
    CEFR — 2-4 qisqa gap ("Sample responses with examiner comments.pdf").
  - O'quvchi ismi AI'ga yuborilmaydi — faqat topshiriq va insho.
  - Provayder xatosi matni saqlanmaydi, faqat qisqa kod.
  - Bitta so'rov = bitta topshiruv (Vercel 30 s): chaqiruvchi
    exam_online / mock_practice alohida endpointda ishlatadi.

Testda AI["call"] almashtiriladi: fn(system, user_text) -> str.
"""
import base64
import html
import json
import re
from datetime import datetime
from typing import Optional

import mock_marking
import cefr_score as C

# IELTS rasmiy qoidasi: 20 so'z va undan kam javob — Band 1 (bo'sh — 0).
# Bunday javob AI'ga yuborilmaydi.
IELTS_SHORT = 20
ESSAY_MAX_CHARS = 6000    # AI'ga yuboriladigan insho chegarasi
SKILLS = ("ielts_writing", "cefr_writing")


class WritingAIError(Exception):
    """code: no_key | rate_limit | ai_error | bad_reply | shape"""

    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


def _default_call(system: str, user_text: str) -> str:
    from student_app import _ai_reply
    # max_tokens katta: "thinking" modellarida o'ylash tokenlari ham shu
    # chegaraga kiradi — javob kesilib qolmasin (2026-09-28 ko'rigi)
    return _ai_reply(system, [{"role": "user", "text": user_text}],
                     max_tokens=6000, temperature=0.1, json_mode=True,
                     per_call=18)


AI = {"call": None}


def _call(system: str, user_text: str) -> str:
    fn = AI.get("call") or _default_call
    try:
        return fn(system, user_text)
    except WritingAIError:
        raise
    except RuntimeError as e:
        if "no-key" in str(e):
            raise WritingAIError("no_key") from None
        raise WritingAIError("ai_error") from None
    except TimeoutError:
        raise WritingAIError("rate_limit") from None
    except LookupError as e:
        # Kalit rad etildi (401/403) — qayta urinishdan foyda yo'q
        if "authentication" in str(e).lower():
            raise WritingAIError("no_key") from None
        raise WritingAIError("ai_error") from None
    except Exception:
        raise WritingAIError("ai_error") from None


# ------------------------------------------------------------ yordamchi
def words(text) -> int:
    """So'z soni — sahifadagi sanagich bilan bir xil (bo'shliq bo'yicha)."""
    return len(re.findall(r"\S+", str(text or "")))


def svg_text(image) -> str:
    """IELTS Task 1 grafigi SVG — undagi yozuvlar (sarlavha, o'qlar,
    qiymatlar) AI'ga matn bo'lib boradi. SVG bo'lmasa bo'sh."""
    s = str(image or "")
    m = re.match(r"data:image/svg\+xml;base64,(.+)$", s, re.S)
    if not m:
        return ""
    try:
        svg = base64.b64decode(m.group(1)).decode("utf-8", "ignore")
    except Exception:
        return ""
    out = []
    for t in re.findall(r"<text\b[^>]*>(.*?)</text>", svg, re.S):
        t = re.sub(r"<[^>]+>", " ", t)
        t = html.unescape(re.sub(r"\s+", " ", t).strip())
        if t:
            out.append(t)
    return " | ".join(out)[:4000]


def skill_of(parts) -> Optional[str]:
    """ielts_writing / cefr_writing — faqat mock Writing baholanadi."""
    from exam_online import _mock_section
    sk = _mock_section(parts or [])
    return sk if sk in SKILLS else None


def tasks_of(parts) -> list:
    """Insho topshiriqlari tartib bilan: har biriga matn va sharoit."""
    out = []
    for p in parts or []:
        for q in p.get("questions") or []:
            if (q.get("type") or "") != "essay":
                continue
            out.append({
                "qid": str(q.get("id") or ""),
                "n": q.get("n"),
                "prompt": str(q.get("q") or "").strip(),
                "instructions": str(p.get("instructions") or "").strip()[:1500],
                "passage": str(p.get("passage") or "").strip()[:2000],
                "min_words": int(q.get("min_words") or 0),
                "chart": svg_text(q.get("image")),
            })
    return out


def _json(raw: str) -> dict:
    m = re.search(r"\{.*\}", str(raw or ""), re.S)
    if not m:
        raise WritingAIError("bad_reply")
    try:
        d = json.loads(m.group(0))
    except (ValueError, TypeError):
        raise WritingAIError("bad_reply") from None
    if not isinstance(d, dict) or not isinstance(d.get("tasks"), list):
        raise WritingAIError("bad_reply")
    return d


def _int(v, lo: int, hi: int) -> Optional[int]:
    try:
        x = int(round(float(v)))
    except (TypeError, ValueError):
        return None
    return max(lo, min(hi, x))


def _feedback(v) -> str:
    # IELTS examiner izohi — bitta paragraf (4-7 gap), inglizcha
    s = re.sub(r"\s+", " ", str(v or "")).strip()
    return s[:1500]


MAX_ERRORS = 12           # har turdan (grammatika / lug'at) bitta topshiriqda


def _errors(v) -> list:
    """Xatolar ro'yxati (2026-09-28, Jahongir: "Grammar mistakes,
    vocabulary mistakes alohida har bir korsatilsin bitta bitta"):
    [{"wrong": asl, "right": to'g'risi, "why": qisqa sabab}]."""
    out = []
    for e in v if isinstance(v, list) else []:
        if not isinstance(e, dict):
            continue
        w = re.sub(r"\s+", " ", str(e.get("wrong") or "")).strip()[:200]
        r = re.sub(r"\s+", " ", str(e.get("right") or "")).strip()[:200]
        why = re.sub(r"\s+", " ", str(e.get("why") or "")).strip()[:120]
        if not w or not r or w == r:
            continue
        # serious — xato ma'noni buzadi (band'ni aynan shu hal qiladi)
        out.append({"wrong": w, "right": r, "why": why,
                    "serious": e.get("serious") is True})
        if len(out) >= MAX_ERRORS:
            break
    return out


ERRORS_RULE = """ERRORS — list the candidate's mistakes one by one, in two separate
lists, in the order they appear (if there are more than {n}, keep the
{n} most important):
- "grammar" (the grammar criterion): verb tense and form,
  subject-verb agreement, articles and determiners, singular/plural and
  countability, word order, fragments, run-ons and comma splices,
  relative clauses and conditionals, grammatical prepositions, verb
  patterns, punctuation;
- "vocabulary" (the vocabulary criterion): wrong word or meaning,
  collocation (e.g. "make a crime"), word formation (e.g. "substantially
  growth"), spelling, register (informal word in formal writing),
  L1-influenced coinages, misused idioms, repetition.
Each item: "wrong" = the exact words copied from the answer (short),
"right" = the corrected words, "why" = a short reason in English
(max 8 words, e.g. "subject-verb agreement", "wrong collocation",
"spelling"), "serious" = true only if the mistake blocks or changes the
meaning for the reader. Do not list British/American spelling variants
or acceptable stylistic choices; do not invent mistakes. Empty list if
there are none.""".format(n=MAX_ERRORS)


def _pick(rows: list, tid: str, i: int, total: int):
    """AI javobidan shu topshiriq qatori: "T1"/"T2"… identifikatori
    bo'yicha (savol raqami "Task 2" bilan chalkashmasin), bo'lmasa
    tartib bo'yicha (qatorlar soni teng bo'lsa)."""
    r = next((x for x in rows if str(x.get("id") or "").strip().upper() == tid), None)
    if r is None and len(rows) == total:
        r = rows[i]
    if r is None:
        raise WritingAIError("bad_reply")
    return r


# ------------------------------------------------------------ IELTS
IELTS_SYSTEM = """You are a senior certified IELTS Academic Writing examiner.
Mark each task by the public IELTS Writing band descriptors (May 2023).
Give each criterion a WHOLE band from 0 to 9:
- ta: Task 1 = Task Achievement; Task 2 = Task Response.
- cc: Coherence and Cohesion.
- lr: Lexical Resource.
- gra: Grammatical Range and Accuracy.
HOW TO FIX A BAND: start from the band that looks closest. The answer
must show ALL the positive features of a band to get it; if one is
missing, go one band lower. When torn between two bands, give the
lower. Key boundaries:
Task 1 ta: 5 = details listed mechanically, no real overview, key
features not adequately covered or not supported with data; 6 = an
overview is attempted, key features adequately highlighted and
supported with figures, some details irrelevant, inaccurate or missing;
7 = a CLEAR overview of the main trends or differences, data logically
grouped, accurate with only a few lapses; 8 = key features skilfully
selected and well illustrated throughout. Task 1 reports only what the
figure shows: invented reasons or opinions are irrelevant content.
Task 2 ta: 5 = a main part of the question is not addressed or only
touched on, or the position is unclear or shifts, ideas limited and
underdeveloped; 6 = every main part addressed (perhaps unevenly) with a
relevant position, but ideas thinly developed or the conclusion unclear
or repetitive; 7 = a clear position throughout, main ideas extended and
supported (may over-generalise); 8 = ideas consistently well developed
and supported, only occasional lapses. With "to what extent / do you
agree" questions, no clear view means 5 or lower.
cc: 5 = organisation not wholly logical, limited or overused linkers,
repetition caused by poor referencing; a Task 2 answer without proper
paragraphs is capped at 5; 6 = clear overall progression, but cohesion
is mechanical (e.g. every sentence opens with Firstly / Moreover / In
addition / Also) or faulty, referencing not flexible; 7 = logical
progression throughout, linkers AND reference/substitution used
flexibly with some inaccuracy; 8 = cohesion well managed, occasional
lapses only.
lr: 5 = limited range, frequent repetition, noticeable spelling or
word-formation errors that may cause the reader difficulty; 6 = adequate
range, meaning clear despite imprecise words, some spelling errors that
do not impede (an ambitious but error-prone writer stays at 6); 7 = some
less common items used with awareness of collocation and style, only a
FEW errors; 8 = wide, precise, natural vocabulary, occasional slips.
gra: 5 = limited, repetitive range, complex sentences attempted but
mostly faulty, frequent errors that cause some difficulty; 6 = a mix of
simple and complex sentences, errors rarely impede but fewer than half
the sentences are error-free; 7 = a variety of complex structures AND
error-free sentences are frequent (about half or more); 8 = the
majority of sentences error-free, errors rare and non-systematic.
PENALTIES: Task 1 under 150 or Task 2 under 250 words loses marks in
ta: slightly short (within about 10%) = ta at most 6; clearly short
(Task 1 under 120, Task 2 under 200) = ta at most 5, and lr/gra may
also suffer. Words copied from the question do not count and earn no
credit; memorised template sentences earn no credit for range. Bullet
points or note form are an inappropriate format (ta and cc). Off-topic
or tangential answers get 4 or lower in ta. Do not reward length alone.
For Task 1, FIGURE TEXT lists only the words and numbers printed on the
chart: if exact values are not given there, judge ta on the overview,
key features and comparisons, and do not penalise figures you cannot
verify.
FEEDBACK — write it in English, in the style of the official IELTS
"Examiner comment": one paragraph of 4-7 sentences that goes through
the criteria in order (task achievement/response, then coherence and
cohesion, then lexical resource, then grammatical range and accuracy)
and agrees with the bands you gave. Be specific: quote short evidence
from the answer in square brackets, e.g. [recieve/receive] or
[Firstly | So | Also], mention if the answer is under the minimum word
count, and say what would be needed for a higher band. Neutral examiner
tone, third person ("The response ...", "There is ..."), no greetings,
no bullet points.
Each task has an id (T1, T2) — copy it.
""" + ERRORS_RULE + """
Reply with JSON only:
{"tasks":[{"id":"T1","ta":<0-9>,"cc":<0-9>,"lr":<0-9>,"gra":<0-9>,"feedback":"...",
"grammar":[{"wrong":"...","right":"...","why":"...","serious":false}],
"vocabulary":[{"wrong":"...","right":"...","why":"...","serious":false}]}]}"""

KEYS = ("ta", "cc", "lr", "gra")


def _ielts_user(todo: list, essays: dict) -> str:
    blocks = []
    for tid, label, t in todo:
        b = [f"### {label} [id={tid}] (minimum {t['min_words'] or '-'} words)",
             f"QUESTION:\n{t['prompt']}"]
        if t["chart"]:
            b.append(f"FIGURE TEXT (words and numbers printed on the chart):\n{t['chart']}")
        e = essays[t["qid"]]
        b.append(f"CANDIDATE'S ANSWER ({words(e)} words):\n{e[:ESSAY_MAX_CHARS]}")
        blocks.append("\n\n".join(b))
    return "\n\n".join(blocks)


def _grade_ielts(tasks: list, answers: dict) -> dict:
    essays = {t["qid"]: str(answers.get(t["qid"]) or "") for t in tasks}
    ids = {t["qid"]: (f"T{i + 1}", f"Task {i + 1}") for i, t in enumerate(tasks)}
    # 0 so'z -> 0; 1-20 so'z -> Band 1 (IELTS qoidasi); qolgani — AI
    todo = [(ids[t["qid"]][0], ids[t["qid"]][1], t) for t in tasks
            if words(essays[t["qid"]]) > IELTS_SHORT]
    got, errs = {}, {}
    if todo:
        d = _json(_call(IELTS_SYSTEM, _ielts_user(todo, essays)))
        rows = [r for r in d["tasks"] if isinstance(r, dict)]
        for i, (tid, _label, t) in enumerate(todo):
            r = _pick(rows, tid, i, len(todo))
            crit = [_int(r.get(k), 0, 9) for k in KEYS]
            if any(c is None for c in crit):
                raise WritingAIError("bad_reply")
            got[t["qid"]] = (crit, _feedback(r.get("feedback")))
            errs[t["qid"]] = (_errors(r.get("grammar")), _errors(r.get("vocabulary")))
    out_tasks = []
    for t in tasks:
        wc = words(essays[t["qid"]])
        if t["qid"] in got:
            crit, fb = got[t["qid"]]
        elif wc > 0:
            crit, fb = [1, 1, 1, 1], ("The response is 20 words or fewer, so it is "
                                      "rated at Band 1 in line with the IELTS rules.")
        else:
            crit, fb = [0, 0, 0, 0], ""
        tb = mock_marking.ielts_band(crit)
        out_tasks.append({
            "qid": t["qid"], "n": t["n"], "label": ids[t["qid"]][1],
            "words": wc, "min_words": t["min_words"],
            "criteria": dict(zip(KEYS, crit)),
            "band": tb["band"] if tb else 0.0,
            "feedback": fb,
            "grammar": errs.get(t["qid"], ([], []))[0],
            "vocabulary": errs.get(t["qid"], ([], []))[1],
            "skipped": t["qid"] not in got,
        })
    # Task 2 ikki barobar og'ir (IELTS): har mezon (T1 + 2*T2) / 3.
    # Yaxlitlash BIR marta — oxirida, mezonlar o'rtachasida (ielts_band)
    if len(out_tasks) == 2:
        a, b = out_tasks[0]["criteria"], out_tasks[1]["criteria"]
        comb = [(a[k] + 2 * b[k]) / 3 for k in KEYS]
    else:
        n = max(1, len(out_tasks))
        comb = [sum(t["criteria"][k] for t in out_tasks) / n for k in KEYS]
    res = mock_marking.compute("ielts_writing", {"marks": comb})
    if res is None:
        raise WritingAIError("shape")
    return {"skill": "ielts_writing", "score": res["band"], "band": res["band"],
            "max": 9.0, "combined": {k: round(v, 2) for k, v in zip(KEYS, comb)},
            "tasks": out_tasks}


# ------------------------------------------------------------ CEFR
# Rasmiy yakuniy shkala (Bilimni baholash agentligi, 2025-10-13) —
# o'z so'zlarimiz bilan, inglizcha (AI uchun). Kalit: WRITING_NEW_PARTS.
CEFR_SCALE = {
    "1.1": [
        "5 = clearly above B1 (B2 or higher): natural, fluent informal email covering the points; one minor slip is fine",
        "4 = higher B1: on topic and covers most task points; simple grammar well controlled, errors appear in complex structures; spelling mostly correct; adequate vocabulary; simple linkers give a linear text; register slips are normal here",
        "3 = lower B1: the same language as 4, but only partly on topic (covers at least one task point)",
        "2 = A2: partly on topic, covers only part of the task; simple sentences with frequent errors that sometimes block meaning; noticeable spelling errors; inadequate vocabulary; may be about 25 words or fewer",
        "1 = A1 or below, mostly in another language, meaningless, or completely off-topic, memorised or copied",
        "0 = no attempt",
    ],
    "1.2": [
        "5 = C1 or above: fully on topic, all task points covered; consistently appropriate formal register; a range of complex structures used accurately with only minor slips; no spelling or punctuation errors; wide vocabulary; varied linking used skilfully",
        "4 = higher B2: on topic, all task points covered; consistent register; some accurate complex structures and errors never cause misunderstanding; a few spelling slips; adequate vocabulary; a limited number of linking devices",
        "3 = lower B2: the same language as 4, but only most task points covered and the register may be inconsistent",
        "2 = B1: covers only part of the task points; register often slips; simple grammar controlled, errors in complex structures; simple linkers; may be short (25-60 words)",
        "1 = A2: partly on topic, no awareness of register; frequent errors even in simple sentences that often block meaning; may be 24 words or fewer",
        "0 = below A2, meaningless, completely off-topic, memorised or copied, mostly in another language, or no attempt",
    ],
    "2": [
        "6 = clearly above C1",
        "5 = C1: fully answers the question with a clear stance and relevant, coherently developed arguments; register fits the genre; many varied complex structures, minor slips only; error-free spelling and punctuation; wide, varied vocabulary; clear paragraphs and skilful, varied linkers",
        "4 = higher B2: answers the question clearly with an evident stance, minor digressions allowed; appropriate register; some accurate complex structures and errors do not mislead; a few spelling slips; adequate vocabulary; clear structure with some connectors, logical flow and paragraphs",
        "3 = lower B2: mostly relevant but EITHER the stance is unclear OR there are off-topic parts; register may not fully fit; language as in 4; organised, but transitions unclear or mechanical; may be unfinished",
        "2 = B1: a weak stance AND digressions; register often slips; simple grammar controlled, errors in complex structures; simple linkers; may be 38-90 words",
        "1 = A2: limited focus, ideas unclear or partly off-topic; frequent errors even in simple sentences; may be 37 words or fewer",
        "0 = below A2, meaningless, completely off-topic, memorised or copied, mostly in another language, or no attempt",
    ],
}

# Yakuniy shkaladagi hajm chegaralari: (so'z <= N) -> ball ko'pi bilan M.
CEFR_LENGTH_CAPS = {"1.1": [(25, 2)],
                    "1.2": [(24, 1), (60, 2)],
                    "2": [(37, 1), (90, 2)]}


def _length_cap(part: str, wc: int) -> Optional[int]:
    for most, cap in CEFR_LENGTH_CAPS.get(part, []):
        if wc <= most:
            return cap
    return None


def _cefr_scale_text() -> str:
    lines = []
    for part, mx, lvl, ln in C.WRITING_NEW_PARTS:
        ln = ln.replace("so'z", "words")
        lines.append(f"Task {part} (target {lvl}, {ln}), mark 0-{mx}:")
        lines.extend(f"  {s}" for s in CEFR_SCALE[part])
    return "\n".join(lines)


CEFR_SYSTEM = """You are a certified rater of the Uzbekistan national CEFR
Multilevel English exam (Writing, new 3-task format, final 2025 scale).
Give each task ONE holistic WHOLE mark on its official scale:
{scale}
HOW TO FIX A MARK:
1. Coverage first. Tasks 1.1 and 1.2 answer the INPUT TEXT, which
contains the points the candidate must respond to. 1.2 needs ALL points
for 4-5; most points = 3; only part of them = 2 or lower. 1.1: most
points = 4; at least one = 3.
2. Part 2: stance and relevance first. A clear position held throughout
with relevant arguments is needed for 4-5; an unclear stance OR
digressions = 3; both = 2. A "both sides" text with no stated view has
an unclear stance.
3. Then place the language on the CEFR ladder: simple structures
controlled but errors in complex ones = B1; some accurate complex
structures with errors that never mislead = B2; many varied complex
structures, only minor slips and error-free spelling = C1.
4. Error impact decides between levels: errors that do not cause
misunderstanding = B2 or higher; errors that sometimes cause
misunderstanding = B1 (one word choice that blocks meaning is enough);
frequent errors in simple sentences that often block meaning = A2.
5. Register barely matters in 1.1; it must be consistently formal for
1.2 marks 4-5 (watch for slang, contractions, "And," openings, a missing
or informal greeting and sign-off) and fit the genre for Part 2 marks
4-5.
6. Give 1.1 a 5 when the email is natural and clearly above B1 (fluent
informal phrasing, contractions, full coverage) even with one minor
slip.
7. In 1.1 a memorised, off-topic or mostly non-English text gets 1; in
1.2 and Part 2 it gets 0.
Be consistent and conservative like a real rater: when torn between two
marks, give the lower.
FEEDBACK — write it in English, in the style of the official Multilevel
"Examiner's comment": 2-5 short sentences built from the scale wording,
in this order: relevance and coverage of the task points; register
(1.1, 1.2) or stance (Part 2); range of structures; vocabulary; whether
errors in grammar and word choice cause misunderstanding; cohesion.
For example: "The response is on topic, but not all the points are
addressed. The register is appropriate. Some complex structures are
used and vocabulary is sufficient for the topic. Errors in grammar and
word choice do not cause misunderstanding. Some cohesive devices and
referencing are used." For a top-mark 1.1 one sentence is enough
("The response is beyond level B1."). Neutral examiner tone, no
greetings.
Each task has an id (T1, T2, T3) — copy it.
""" + ERRORS_RULE + """
Reply with JSON only:
{{"tasks":[{{"id":"T1","mark":<whole number>,"feedback":"...",
"grammar":[{{"wrong":"...","right":"...","why":"...","serious":false}}],
"vocabulary":[{{"wrong":"...","right":"...","why":"...","serious":false}}]}}]}}"""


def _cefr_user(todo: list, essays: dict) -> str:
    blocks = []
    for tid, t, (part, mx, _lv, _ln) in todo:
        b = [f"### Task {part} [id={tid}] (mark 0-{mx}, minimum {t['min_words'] or '-'} words)"]
        if t["instructions"]:
            b.append(f"INSTRUCTIONS:\n{t['instructions']}")
        if t["passage"]:
            b.append(f"INPUT TEXT:\n{t['passage']}")
        b.append(f"QUESTION:\n{t['prompt']}")
        e = essays[t["qid"]]
        b.append(f"CANDIDATE'S ANSWER ({words(e)} words):\n{e[:ESSAY_MAX_CHARS]}")
        blocks.append("\n\n".join(b))
    return "\n\n".join(blocks)


def _grade_cefr(tasks: list, answers: dict) -> dict:
    if len(tasks) != len(C.WRITING_NEW_PARTS):
        raise WritingAIError("shape")
    pairs = list(zip(tasks, C.WRITING_NEW_PARTS))
    essays = {t["qid"]: str(answers.get(t["qid"]) or "") for t in tasks}
    # Bo'sh javob — 0 (AI'siz); qisqasini ham AI baholaydi (shkalada
    # "hajm yetmasa ball tushadi")
    todo = [(f"T{i + 1}", t, spec) for i, (t, spec) in enumerate(pairs)
            if words(essays[t["qid"]]) > 0]
    got, errs = {}, {}
    if todo:
        system = CEFR_SYSTEM.format(scale=_cefr_scale_text())
        d = _json(_call(system, _cefr_user(todo, essays)))
        rows = [r for r in d["tasks"] if isinstance(r, dict)]
        for i, (tid, t, spec) in enumerate(todo):
            r = _pick(rows, tid, i, len(todo))
            mk = _int(r.get("mark"), 0, spec[1])
            if mk is None:
                raise WritingAIError("bad_reply")
            fb = _feedback(r.get("feedback"))
            # 1.1 da 0 faqat bo'sh javobga (yozilgan har narsa kamida 1)
            if spec[0] == "1.1":
                mk = max(mk, 1)
            wc = words(essays[t["qid"]])
            cap = _length_cap(spec[0], wc)
            if cap is not None and mk > cap:
                mk = cap
                fb = (fb + f" At {wc} words the response is too short for a "
                      f"mark above {cap}.").strip()
            got[t["qid"]] = (mk, fb)
            errs[t["qid"]] = (_errors(r.get("grammar")), _errors(r.get("vocabulary")))
    out_tasks, marks = [], []
    for t, (part, mx, _lv, _ln) in pairs:
        mk, fb = got.get(t["qid"], (0, ""))
        marks.append(mk)
        out_tasks.append({
            "qid": t["qid"], "n": t["n"], "part": part, "label": f"Task {part}",
            "words": words(essays[t["qid"]]), "min_words": t["min_words"],
            "mark": mk, "max": mx,
            "level": C.writing_new_band_level(part, mk),
            "feedback": fb,
            "grammar": errs.get(t["qid"], ([], []))[0],
            "vocabulary": errs.get(t["qid"], ([], []))[1],
            "skipped": t["qid"] not in got,
        })
    res = mock_marking.compute("cefr_writing", {"marks": marks})
    if res is None:
        raise WritingAIError("shape")
    return {"skill": "cefr_writing", "score": res["score"], "max": 75,
            "level": res["level"], "exact": bool(res.get("exact")),
            "raw": res.get("raw"), "tasks": out_tasks}


# ------------------------------------------------------------ kirish
def grade(parts, answers) -> dict:
    """Bitta topshiruvning Writing bahosi. Xato bo'lsa WritingAIError."""
    skill = skill_of(parts)
    if not skill:
        raise WritingAIError("shape")
    tasks = tasks_of(parts)
    if not tasks:
        raise WritingAIError("shape")
    ans = answers if isinstance(answers, dict) else {}
    res = (_grade_ielts(tasks, ans) if skill == "ielts_writing"
           else _grade_cefr(tasks, ans))
    res["at"] = datetime.utcnow().isoformat(timespec="seconds")
    return res
