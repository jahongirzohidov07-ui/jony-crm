"""Проверка дополнительных текстов для аудирования. Запуск: python scripts/test-russian-listening.py."""
import json
import re
import unittest
from collections import Counter
from difflib import SequenceMatcher
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "src/data/russian/listening-extended.json"
FIELDS = {"month", "lesson", "title", "format", "levelNote", "preListening",
          "firstTask", "questions", "lines", "followUp", "teacherNotes"}
FORMATS = {"Диалог", "Голосовое сообщение", "Телефонный разговор", "Объявление"}
# Диапазоны дают редактору свободу, сохраняя постепенное усложнение.
BOUNDS = [(50, 70), (70, 90), (85, 105), (100, 125), (115, 140),
          (130, 155), (145, 170), (155, 180), (165, 190),
          (180, 230), (180, 230), (180, 230)]


def words(text):
    return re.findall(r"[А-Яа-яЁё]+(?:-[А-Яа-яЁё]+)*", text)


def normalize(text):
    return " ".join(words(text.lower().replace("ё", "е")))


def script(item):
    return " ".join(line["text"] for line in item["lines"])


def strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, list):
        for child in value:
            yield from strings(child)
    elif isinstance(value, dict):
        for key, child in value.items():
            if key != "speaker":
                yield from strings(child)


class ListeningTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.items = json.loads(DATA.read_text(encoding="utf-8"))

    def test_months_and_practice_placement(self):
        self.assertIsInstance(self.items, list)
        self.assertEqual(len(self.items), 12)
        self.assertEqual([x["month"] for x in self.items], list(range(1, 13)))
        source = []
        for part in range(1, 5):
            source.extend(json.loads((ROOT / f"src/data/russian/part-{part}.json").read_text(encoding="utf-8")))
        by_number = {x["no"]: x for x in source}
        for x in self.items:
            with self.subTest(month=x["month"]):
                self.assertIs(type(x["month"]), int)
                self.assertIs(type(x["lesson"]), int)
                self.assertEqual(x["lesson"], x["month"] * 12 - 1)
                self.assertEqual(by_number[x["lesson"]]["month"], x["month"])
                self.assertEqual(by_number[x["lesson"] + 1]["month"], x["month"])

    def test_exact_schema(self):
        for x in self.items:
            with self.subTest(month=x["month"]):
                self.assertEqual(set(x), FIELDS)
                for field in ("title", "format", "levelNote", "preListening", "followUp", "teacherNotes"):
                    self.assertIsInstance(x[field], str)
                    self.assertTrue(x[field].strip())
                self.assertIn(x["format"], FORMATS)
                self.assertIsInstance(x["firstTask"], dict)
                self.assertEqual(set(x["firstTask"]), {"prompt", "answer"})
                self.assertIsInstance(x["questions"], list)
                self.assertEqual(len(x["questions"]), 5)
                for q in x["questions"]:
                    self.assertEqual(set(q), {"prompt", "answer", "evidence"})
                    for value in q.values():
                        self.assertIsInstance(value, str)
                        self.assertTrue(value.strip())
                for value in x["firstTask"].values():
                    self.assertIsInstance(value, str)
                    self.assertTrue(value.strip())
                self.assertIsInstance(x["lines"], list)
                self.assertTrue(x["lines"])
                for line in x["lines"]:
                    self.assertEqual(set(line), {"speaker", "text"})
                    self.assertIn(line["speaker"], {"A", "B"})
                    self.assertIsInstance(line["text"], str)
                    self.assertTrue(line["text"].strip())

    def test_word_count_progression(self):
        counts = [len(words(script(x))) for x in self.items]
        for x, count, (low, high) in zip(self.items, counts, BOUNDS):
            with self.subTest(month=x["month"], words=count):
                self.assertGreaterEqual(count, low)
                self.assertLessEqual(count, high)
        for earlier, later in zip(counts, counts[1:]):
            self.assertGreater(later, earlier, "Объём должен постепенно расти")

    def test_exact_evidence_in_spoken_lines(self):
        for x in self.items:
            for q in x["questions"]:
                with self.subTest(month=x["month"], question=q["prompt"]):
                    # Не нормализуем: регистр, пунктуация и буква ё должны совпадать.
                    self.assertTrue(any(q["evidence"] in line["text"] for line in x["lines"]), q["evidence"])
                    self.assertGreaterEqual(len(words(q["evidence"])), 2)
            self.assertEqual(len({normalize(q["prompt"]) for q in x["questions"]}), 5)
            self.assertEqual(len({q["evidence"] for q in x["questions"]}), 5)
            self.assertNotIn(normalize(x["firstTask"]["prompt"]), {normalize(q["prompt"]) for q in x["questions"]})

    def test_varied_formats_and_voices(self):
        distribution = Counter(x["format"] for x in self.items)
        self.assertEqual(set(distribution), FORMATS)
        self.assertTrue(all(count >= 2 for count in distribution.values()))
        for x in self.items:
            speakers = [line["speaker"] for line in x["lines"]]
            if x["format"] in {"Диалог", "Телефонный разговор"}:
                self.assertEqual(set(speakers), {"A", "B"})
                self.assertTrue(all(a != b for a, b in zip(speakers, speakers[1:])))
                self.assertGreaterEqual(min(Counter(speakers).values()), 2)
            else:
                self.assertEqual(set(speakers), {"A"})

    def test_original_and_distinct_scripts(self):
        self.assertEqual(len({normalize(x["title"]) for x in self.items}), 12)
        texts = [normalize(script(x)) for x in self.items]
        self.assertEqual(len(set(texts)), 12)
        for i, first in enumerate(texts):
            for second in texts[i + 1:]:
                self.assertLess(SequenceMatcher(None, first, second, autojunk=False).ratio(), 0.75)
        # Сверяем с исходными диалогами, не изменяя исходники и переводы.
        for part in range(1, 5):
            originals = json.loads((ROOT / f"src/data/russian/part-{part}.json").read_text(encoding="utf-8"))
            for lesson in originals:
                dialog_text = normalize(" ".join(strings(lesson.get("dialog", []))))
                if len(words(dialog_text)) >= 20:
                    for text in texts:
                        self.assertNotEqual(text, dialog_text)
                        self.assertNotIn(text, dialog_text)

    def test_russian_without_translation_dependency(self):
        for x in self.items:
            for value in strings(x):
                with self.subTest(month=x["month"], text=value[:50]):
                    self.assertRegex(value, r"[А-Яа-яЁё]")
                    self.assertNotRegex(value, r"[A-Za-zЎўҚқҒғҲҳ]")
                    self.assertNotIn("\ufffd", value)

    def test_scaffolding_and_differentiation(self):
        for x in self.items:
            with self.subTest(month=x["month"]):
                self.assertGreaterEqual(len(words(x["preListening"])), 12)
                self.assertGreaterEqual(len(words(x["teacherNotes"])), 25)
                self.assertGreaterEqual(len(words(x["followUp"])), 20)
                self.assertRegex(x["followUp"].lower(), r"опора|поддержка")
                self.assertRegex(x["followUp"].lower(), r"сильн|усложнение")


if __name__ == "__main__":
    unittest.main(verbosity=2)
