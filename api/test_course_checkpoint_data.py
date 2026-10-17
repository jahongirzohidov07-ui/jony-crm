"""Offline contract and editorial regression checks for weekly transfer bosses.

Run: python -B -m unittest discover -s api -p test_course_checkpoint_data.py
No app/database imports, generated content, network access or runtime AI.

The lesson references below document the manually reviewed grammar prerequisites,
not a claim that regex can establish pedagogical correctness. Full answer leakage
is checked as a token sequence (not substrings such as 'is' inside 'this').
Reorder tasks may contain the answer's words, but never its completed sequence.
"""
import copy
import json
import re
import unittest
from pathlib import Path

API = Path(__file__).resolve().parent
COUNTS = {"en": 32, "de": 24}
PACE = {"en": 6, "de": 3}

# One canonical prerequisite lesson per authored question, in question order.
# Review weeks deliberately reuse earlier grammar in new contexts.
PREREQUISITES = {
    "en": [
        (1, 5, 5), (7, 7, 8), (13, 17, 13), (21, 20, 20),
        (25, 25, 29), (31, 32, 33), (37, 37, 39), (45, 46, 47),
        (51, 52, 49), (55, 55, 58), (63, 61, 65), (67, 66, 67),
        (73, 74, 76), (79, 80, 82), (88, 89, 89), (95, 93, 95),
        (99, 100, 99), (106, 104, 105), (109, 112, 111),
        (118, 119, 116), (124, 121, 122), (128, 130, 130),
        (137, 137, 136), (139, 143, 140), (146, 147, 148),
        (154, 154, 151), (158, 157, 161), (31, 146, 152),
        (76, 119, 158), (109, 100, 112), (128, 137, 143),
        (158, 154, 147),
    ],
    "de": [
        (2, 2, 3), (6, 6, 5), (8, 8, 9), (11, 12, 10),
        (13, 15, 15), (16, 17, 18), (20, 21, 19),
        (22, 23, 24), (26, 26, 26), (28, 29, 30),
        (31, 33, 33), (36, 36, 34), (39, 38, 39),
        (41, 42, 42), (43, 45, 43), (46, 48, 46),
        (49, 50, 51), (52, 53, 52), (56, 57, 55),
        (59, 60, 58), (61, 61, 63), (64, 65, 66),
        (67, 68, 69), (66, 59, 63),
    ],
}


# One independently audited current-week anchor per checkpoint. The topic is an
# actual canonical grammar exercise family, NOT a lesson/checkpoint title.
# Format: boss question (1-based), canonical lesson, family, focus, answer regex.
# Other two questions may exercise any previously taught cumulative material.
WEEKLY_TARGETS = {
    "en": [
        (1, 1, "1.2", "adjective before noun", r"green cup"),
        (1, 7, "2.2", "be + adjective", r"are \w+"),
        (1, 13, "3.2", "regular plural -es", r"small \w+es"),
        (1, 21, "4.7", "plural demonstrative", r"those \w+ \w+s"),
        (1, 25, "5.2", "there are", r"are three \w+s"),
        (1, 31, "6.3", "third person -es", r"\w+es cups"),
        (1, 37, "7.1", "present continuous", r"is \w+ing bread"),
        (1, 45, "8.9", "position preposition", r"under the \w+"),
        (1, 51, "9.10", "irregular past simple", r"bought \w+"),
        (1, 55, "10.1", "past continuous", r"was \w+ing a chair"),
        (1, 63, "11.7", "going to intention", r"am going to \w+ the shelf"),
        (1, 67, "12.3", "present perfect has", r"has lost her \w+"),
        (1, 73, "13.1", "present perfect continuous", r"has been \w+ing the radio"),
        (1, 79, "14.1", "short comparative", r"\w+er than the road"),
        (1, 88, "15.9", "future ability", r"will be able to \w+ maps"),
        (1, 95, "16.16", "unnecessary completed action", r"needn't have bought extra bread"),
        (1, 99, "17.7", "past deduction", r"must have taken the wrong road"),
        (1, 106, "18.10", "second conditional result", r"would visit that island"),
        (1, 109, "19.1", "third conditional result", r"would have caught the ferry"),
        (1, 118, "20.8", "present continuous passive", r"is being \w+ed"),
        (1, 124, "21.10", "past perfect passive", r"had been \w+ed"),
        (1, 128, "22.4", "reported continuous backshift", r"was \w+ing her suitcase"),
        (1, 137, "23.13", "reduced active relative", r"\w+ing a violin"),
        (1, 139, "24.1", "verb followed by gerund", r"\w+ing at night"),
        (1, 146, "25.6", "despite followed by gerund", r"\w+ing nervous"),
        (1, 154, "26.11", "indirect wh question", r"the painter lives"),
        (1, 158, "27.5", "future perfect", r"will have \w+ed the lights"),
        (1, 166, "6.2", "review: third person present", r"explains the rules"),
        (1, 173, "13.13", "review: past perfect continuous", r"had been \w+ing bricks"),
        (1, 179, "19.1", "review: third conditional", r"would have found the village"),
        (1, 183, "22.5", "review: perfect backshift", r"had \w+ed the invoice"),
        (1, 191, "27.5", "review: future perfect", r"will have \w+ed every room"),
    ],
    "de": [
        (1, 2, "g003", "sein in present", r"bin \w+"),
        (1, 6, "g011", "haben in present", r"haben Brot"),
        (1, 8, "g015", "regular present conjugation", r"wohnt in Ulm"),
        (1, 11, "g021", "verb second after time phrase", r"backen wir Brot"),
        (1, 13, "g025", "possessive determiner", r"unser Haus"),
        (1, 16, "g031", "clock-time preposition", r"um halb neun"),
        (1, 20, "g039", "polite wish", r"möchte Suppe"),
        (1, 22, "g043", "dative article", r"dem Mädchen"),
        (1, 26, "g051", "strong participle perfect", r"habe eine Birne gegessen"),
        (1, 28, "g055", "separable participle", r"hat im Dorf eingekauft"),
        (1, 31, "g061", "haben preterite", r"hatten wenig Geld"),
        (1, 36, "g071", "future auxiliary and infinitive", r"wirst deine Oma besuchen"),
        (1, 39, "g077", "two-way preposition location", r"den Eltern"),
        (1, 41, "g081", "definite accusative adjective", r"alten Baum"),
        (1, 43, "g086", "comparative", r"höher als das Haus"),
        (1, 46, "g092", "indirect yes-no question", r"das Museum heute öffnet"),
        (1, 49, "g097", "genitive article and noun", r"des Fahrrads"),
        (1, 52, "g107", "pluperfect", r"hatte er das Büro verlassen"),
        (1, 56, "g117", "purpose infinitive", r"Geld zu sparen"),
        (1, 59, "g123", "dative relative", r"dem ich vertraue"),
        (1, 61, "g127", "hypothetical würde", r"würde ich nach Peru reisen"),
        (1, 64, "g133", "present process passive", r"wird gekocht"),
        (1, 67, "g139", "verb-preposition accusative", r"an ihren Bruder"),
        (3, 72, "g132", "review: hypothetical condition result", r"würde ich ein Klavier kaufen"),
    ],
}


def current_week_errors(data, canonical):
    """Check concrete source families and the audited target's grammatical form.

    These regression checks preserve the human-reviewed mapping. They are not an
    automatic proof of every possible sentence's grammatical or semantic quality.
    """
    errors = []
    for language, count in COUNTS.items():
        if len(WEEKLY_TARGETS[language]) != count:
            errors.append(language + ": target coverage")
            continue
        lessons = {lesson["lesson"]: lesson for lesson in canonical[language]}
        for week, (index, lesson, family, focus, pattern) in enumerate(WEEKLY_TARGETS[language], 1):
            label = f"{language}:{week}"
            first = (week - 1) * PACE[language] + 1
            last = week * PACE[language]
            if not first <= lesson <= last:
                errors.append(label + ": target outside current week")
            grammar = next(s for s in lessons[lesson]["sections"] if s["id"] == "grammar")
            prefix = (f"{language}:{lesson}:grammar:{family}:"
                      if language == "en" else f"{language}:{lesson}:{family}-")
            evidence = [q for q in grammar["questions"] if q["id"].startswith(prefix)]
            if not evidence or not all(q.get("explanation") for q in evidence):
                errors.append(label + ": missing canonical grammar evidence")
            target = data[language][week - 1]["questions"][index - 1]
            if not re.fullmatch(pattern, target["expected"][0], re.I):
                errors.append(label + ": current-week target changed")
            if target["id"] != f"{language}:boss:{week}:{index}" or not focus:
                errors.append(label + ": target identity")
    return errors


# Supplement the manual audit with broad guards against accidental early use.
GATES = {
    "en": [
        (r"\b(?:am|is|are)\b", 2),
        (r"\b(?:was|were|did|bought)\b", 9),
        (r"\bused to\b", 10),
        (r"\b(?:will|going to)\b", 11),
        (r"\b(?:have|has) (?:not )?(?:lost|chosen|finished)\b", 12),
        (r"\b(?:has been|had been|had eaten)\b", 13),
        (r"\b(?:must|should) have\b", 17),
        (r"\bwould have\b", 19),
        (r"\b(?:is|are) being\b", 20),
        (r"\bwill have\b", 27),
    ],
    "de": [
        (r"\b(?:kann|können|müsst)\b", 6),
        (r"\b(?:möchte|dürft)\b", 7),
        (r"\b(?:habe|hat|haben|sind) .+ (?:gegessen|gefahren|getrunken)\b", 9),
        (r"\b(?:hatten|freue mich|wascht euch)\b", 11),
        (r"\b(?:werde|wirst)\b", 12),
        (r"\bhatte er\b", 18),
        (r"\b(?:würde|wären|solltest)\b", 21),
        (r"\b(?:wird gekocht|wurden repariert|unterschrieben werden)\b", 22),
    ],
}


def tokens(value):
    return tuple(re.findall(r"\w+", value.casefold()))


def contains_sequence(haystack, needle):
    return any(
        haystack[i:i + len(needle)] == needle
        for i in range(len(haystack) - len(needle) + 1)
    )


def source_questions(canonical, language):
    for lesson in canonical[language]:
        for section in lesson["sections"]:
            yield from section["questions"]


def validate(data, canonical):
    """Return all contract/content errors instead of stopping at the first."""
    errors = []
    if set(data) != set(COUNTS):
        errors.append("languages")
    ids, prompts = set(), set()
    for language, count in COUNTS.items():
        weeks = data.get(language, [])
        if [w.get("week") for w in weeks] != list(range(1, count + 1)):
            errors.append(f"{language}: week coverage")
        old = list(source_questions(canonical, language))
        old_prompts = {tokens(q["prompt"]) for q in old}
        old_answers = {tokens(a) for q in old for a in q.get("expected", [])}
        for week in weeks:
            number = week.get("week")
            label = f"{language}:{number}"
            if set(week) != {"week", "title", "questions"}:
                errors.append(label + ": week schema")
            if type(number) is not int or not 1 <= number <= count:
                errors.append(label + ": week number")
                continue
            if not isinstance(week.get("title"), str) or not week["title"].strip():
                errors.append(label + ": title")
            if len(week.get("questions", [])) != 3:
                errors.append(label + ": question count")
            for index, question in enumerate(week.get("questions", []), 1):
                qid = question.get("id")
                if qid != f"{language}:boss:{number}:{index}" or qid in ids:
                    errors.append(label + ": question ID")
                ids.add(qid)
                if set(question) != {"id", "prompt", "expected", "explanation", "caseSensitive"}:
                    errors.append(label + ": question schema")
                if question.get("caseSensitive") is not False:
                    errors.append(label + ": case sensitivity")
                for field in ("prompt", "explanation"):
                    if not isinstance(question.get(field), str) or not question[field].strip():
                        errors.append(label + ": " + field)
                prompt = question.get("prompt", "")
                pt = tokens(prompt)
                if pt in prompts or pt in old_prompts:
                    errors.append(label + ": copied prompt")
                prompts.add(pt)
                if "Faqat javob" not in prompt:
                    errors.append(label + ": response instruction")
                if re.search(r"(?:^|\n)[A-D][.)] ", prompt):
                    errors.append(label + ": multiple choice")
                answers = question.get("expected")
                if not isinstance(answers, list) or not answers:
                    errors.append(label + ": empty expected")
                    continue
                if any(not isinstance(a, str) or not a.strip() for a in answers):
                    errors.append(label + ": invalid expected")
                    continue
                if len(set(answers)) != len(answers):
                    errors.append(label + ": duplicate variant")
                for answer in answers:
                    at = tokens(answer)
                    if len(at) < 2:
                        errors.append(label + ": trivial answer")
                    if contains_sequence(pt, at):
                        errors.append(label + ": leaked answer")
                    if at in old_answers:
                        errors.append(label + ": copied answer")
                    if answer != answer.strip() or "___" in answer:
                        errors.append(label + ": unfinished answer")
                    for pattern, first_week in GATES[language]:
                        if number < first_week and re.search(pattern, answer, re.I):
                            errors.append(label + ": premature grammar")
    return errors


class CourseCheckpointDataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads((API / "course_checkpoint_data.json").read_text(encoding="utf-8"))
        cls.canonical = json.loads((API / "student_course_practice_data.json").read_text(encoding="utf-8"))

    def test_all_168_questions_and_complete_contract(self):
        self.assertEqual(
            sum(len(w["questions"]) for ws in self.data.values() for w in ws), 168
        )
        self.assertEqual(validate(self.data, self.canonical), [])

    def test_curriculum_references_and_course_lengths(self):
        for language, count in COUNTS.items():
            lessons = {l["lesson"]: l for l in self.canonical[language]}
            self.assertEqual(set(lessons), set(range(1, count * PACE[language] + 1)))
            self.assertEqual(len(PREREQUISITES[language]), count)
            for week, references in enumerate(PREREQUISITES[language], 1):
                self.assertEqual(len(references), 3)
                for lesson in references:
                    with self.subTest(language=language, week=week, lesson=lesson):
                        self.assertLessEqual(lesson, week * PACE[language])
                        self.assertTrue(any(s["id"] == "grammar" for s in lessons[lesson]["sections"]))

    def test_every_week_has_three_distinct_transfer_answers(self):
        for language, weeks in self.data.items():
            for week in weeks:
                answers = [tokens(q["expected"][0]) for q in week["questions"]]
                with self.subTest(language=language, week=week["week"]):
                    self.assertEqual(len(set(answers)), 3)
                    self.assertTrue(all(len(answer) >= 2 for answer in answers))

    def test_all_56_weeks_have_current_week_grammar_evidence(self):
        self.assertEqual(current_week_errors(self.data, self.canonical), [])

    def test_title_only_coverage_is_rejected(self):
        changed = copy.deepcopy(self.data)
        # A plausible cumulative answer is not current-week grammar evidence.
        # Keep the title untouched to prove title matching cannot satisfy this.
        changed["en"][27]["questions"][0]["expected"] = ["the guard left"]
        self.assertIn(
            "en:28: current-week target changed",
            current_week_errors(changed, self.canonical),
        )

    def test_missing_canonical_family_is_rejected(self):
        changed = copy.deepcopy(self.canonical)
        grammar = next(s for s in changed["de"][71]["sections"] if s["id"] == "grammar")
        grammar["questions"] = [
            q for q in grammar["questions"] if not q["id"].startswith("de:72:g132-")
        ]
        self.assertIn(
            "de:24: missing canonical grammar evidence",
            current_week_errors(self.data, changed),
        )

    def test_reviewed_alternative_answers_remain_accepted(self):
        # Independent editorial review: equally grammatical target fragments.
        alternatives = {
            "en:boss:8:1": "beneath the bed",
            "en:boss:19:3": "would be living in Rome",
            "de:boss:17:1": "des Fahrrades",
            "de:boss:21:2": "würden wir entspannter sein",
        }
        questions = {
            q["id"]: q for weeks in self.data.values()
            for week in weeks for q in week["questions"]
        }
        for qid, alternative in alternatives.items():
            with self.subTest(question=qid, alternative=alternative):
                self.assertIn(alternative, questions[qid]["expected"])
                self.assertIs(questions[qid]["caseSensitive"], False)

    def test_missing_week_is_rejected(self):
        changed = copy.deepcopy(self.data)
        changed["de"].pop()
        self.assertIn("de: week coverage", validate(changed, self.canonical))

    def test_duplicate_ids_are_rejected(self):
        changed = copy.deepcopy(self.data)
        changed["en"][0]["questions"][1]["id"] = "en:boss:1:1"
        self.assertIn("en:1: question ID", validate(changed, self.canonical))

    def test_token_normalized_leaks_are_rejected(self):
        changed = copy.deepcopy(self.data)
        changed["en"][0]["questions"][0]["prompt"] += " GREEN / CUP!"
        self.assertIn("en:1: leaked answer", validate(changed, self.canonical))
        self.assertFalse(contains_sequence(tokens("this island"), tokens("is")))

    def test_options_are_rejected(self):
        changed = copy.deepcopy(self.data)
        changed["de"][0]["questions"][0]["options"] = ["bin", "ist"]
        self.assertIn("de:1: question schema", validate(changed, self.canonical))

    def test_copied_source_answer_is_rejected(self):
        changed = copy.deepcopy(self.data)
        original = next(
            a for q in source_questions(self.canonical, "en")
            for a in q.get("expected", []) if len(tokens(a)) >= 2
        )
        changed["en"][0]["questions"][0]["expected"] = [original]
        self.assertIn("en:1: copied answer", validate(changed, self.canonical))

    def test_premature_advanced_grammar_is_rejected(self):
        changed = copy.deepcopy(self.data)
        changed["en"][0]["questions"][0]["expected"] = ["will have examined every room"]
        changed["de"][0]["questions"][0]["expected"] = ["würde ich ein Klavier kaufen"]
        errors = validate(changed, self.canonical)
        self.assertIn("en:1: premature grammar", errors)
        self.assertIn("de:1: premature grammar", errors)

    def test_upper_weeks_retain_advanced_grammar(self):
        # Guard against replacing the final bosses with beginner noun drills.
        en = " ".join(q["expected"][0] for w in self.data["en"][27:] for q in w["questions"])
        de = " ".join(q["expected"][0] for w in self.data["de"][20:] for q in w["questions"])
        for phrase in ("had been laying", "would have found", "will have examined"):
            self.assertIn(phrase, en)
        for phrase in ("würde ich", "unterschrieben werden", "mit denen ich arbeite"):
            self.assertIn(phrase, de)


if __name__ == "__main__":
    unittest.main()
