"""SQLite integration tests; no production database or external services."""
import copy
import json
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
os.environ["DATABASE_URL"] = "sqlite://"
os.environ["JONY_CRM_SECRET"] = "russian-course-test-secret-only"
sys.path.insert(0, str(ROOT / "api"))

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, inspect, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import models
from auth import create_access_token
from database import Base, get_db
import student_russian as russian
from student_russian_models import StudentRussianProgress

PREFIX = "/api/student/russian"


class RussianCourseTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite://", connect_args={"check_same_thread": False},
                                    poolclass=StaticPool)
        Base.metadata.create_all(self.engine)
        self.sessions = sessionmaker(bind=self.engine)
        app = FastAPI()
        app.include_router(russian.router)
        def database():
            with self.sessions() as db:
                yield db
        app.dependency_overrides[get_db] = database
        self.client = TestClient(app)
        with self.sessions() as db:
            for i, (role, active, status) in enumerate([
                ("student", 1, "active"), ("student", 1, "active"),
                ("teacher", 1, None), ("student", 0, "active"),
                ("student", 1, "frozen"), ("student", 1, "archived"),
                ("student", 1, None)], 1):
                db.add(models.User(id=i, username=f"user{i}", full_name=f"User {i}",
                                   password_hash="unused", role=role, is_active=active))
                if status:
                    db.add(models.Student(id=i, user_id=i, full_name=f"Student {i}",
                                          status=status))
            db.commit()

    def tearDown(self):
        self.client.close()
        self.engine.dispose()

    def headers(self, user=1):
        return {"Authorization": "Bearer " + create_access_token({"sub": f"user{user}"})}

    def get(self, path, user=1):
        return self.client.get(PREFIX + path, headers=self.headers(user))

    def check(self, answers, kind="grammar", no=1, user=1, **extra):
        return self.client.post(PREFIX + f"/lessons/{no}/check",
                                headers=self.headers(user),
                                json={"kind": kind, "answers": answers, **extra})

    def test_exact_source_parity_and_no_teacher_content(self):
        source = []
        for part in range(1, 5):
            source += json.loads((ROOT / f"src/data/russian/part-{part}.json").read_text("utf-8"))
        fields = {"no", "month", "title", "objective", "grammar", "phrases", "dialog",
                  "questions", "homework", "exit", "roleplay"}
        self.assertEqual(russian.LESSONS, [{k: v for k, v in row.items() if k in fields}
                                          for row in source])
        self.assertEqual(len(source), 144)
        self.assertEqual({row["month"] for row in source}, set(range(1, 13)))
        self.assertNotIn("teacherTip", json.dumps(russian.LESSONS))
        for original in source:
            result = self.get(f'/lessons/{original["no"]}')
            self.assertEqual(result.status_code, 200)
            expected = {k: copy.deepcopy(v) for k, v in original.items() if k in fields}
            expected["grammar"]["exercises"] = [
                {"prompt": e["prompt"]} for e in original["grammar"]["exercises"]]
            self.assertEqual(result.json(), expected)
        listing = self.get("/course").json()
        self.assertEqual(listing["progress"], [])
        self.assertEqual(listing["lessons"], [
            {**{k: row[k] for k in ("no", "month", "title", "objective")},
             "phrase_count": len(row["phrases"]), "grammar_title": row["grammar"]["title"]}
            for row in source])

    def test_real_auth_and_block_status_on_every_route(self):
        for method, path, body in [
            ("GET", "/course", None), ("GET", "/lessons/1", None),
            ("POST", "/lessons/1/check", {"kind": "grammar", "answers": ["", "", ""]})]:
            for user, status in [(None, 401), (3, 403), (4, 401), (5, 403), (6, 403), (7, 403)]:
                response = self.client.request(method, PREFIX + path, json=body,
                    headers=self.headers(user) if user else {})
                self.assertEqual(response.status_code, status, (method, user, response.text))
        self.assertEqual(self.client.get(PREFIX + "/course",
                         headers={"Authorization": "Bearer invalid"}).status_code, 401)
        expired = create_access_token({"sub": "user1"}, minutes=-1)
        self.assertEqual(self.client.get(PREFIX + "/course",
                         headers={"Authorization": "Bearer " + expired}).status_code, 401)

    def test_scoring_normalization_and_explicit_variants(self):
        answers = [e["answer"] for e in russian.LESSONS[0]["grammar"]["exercises"]]
        result = self.check(["  " + a.upper() + "!!!  " for a in answers]).json()
        self.assertEqual((result["score"], result["total"]), (3, 3))
        for result_row, source in zip(result["results"], russian.LESSONS[0]["grammar"]["exercises"]):
            self.assertEqual(result_row, {"correct": True, "answer": source["answer"],
                                         "explanation": source["explanation"]})
        self.assertEqual(self.check(["", "   ", "!!!"]).json()["score"], 0)
        self.assertFalse(russian._matches("Salom", "Assalomu alaykum!"))
        self.assertTrue(russian._matches("  O'zbek   tili! ", "O‘zbek tili."))
        self.assertFalse(russian._matches("", "!!!"))
        explicit = [(l, e) for l in russian.LESSONS for e in l["grammar"]["exercises"]
                    if " / " in e["answer"]]
        self.assertTrue(explicit)
        for lesson, exercise in explicit:
            for variant in exercise["answer"].split(" / "):
                answers = [variant if e is exercise else e["answer"]
                           for e in lesson["grammar"]["exercises"]]
                result = self.check(answers, no=lesson["no"]).json()
                self.assertEqual(result["score"], result["total"])

    def test_vocabulary_canonical_answers(self):
        for lesson in russian.LESSONS:
            answers = [p["uz"] for p in lesson["phrases"]]
            result = self.check(answers, kind="vocabulary", no=lesson["no"]).json()
            self.assertEqual((result["score"], result["total"]), (len(answers), len(answers)))
            self.assertEqual([r["answer"] for r in result["results"]], answers)
        wrong_direction = self.check([p["ru"] for p in russian.LESSONS[0]["phrases"]],
                                     kind="vocabulary").json()
        self.assertEqual(wrong_direction["score"], 0)

    def test_strict_validation_and_missing_lessons(self):
        for answers in [[], ["x"], ["x"] * 4, [True, "", ""], [1, "", ""],
                        [None, "", ""], [{}, "", ""], "abc", None]:
            self.assertEqual(self.check(answers).status_code, 422, answers)
        for kind in ["unknown", True, 1, None]:
            self.assertEqual(self.check([""] * 3, kind=kind).status_code, 422)
        self.assertEqual(self.check([""] * 3, student_id=2).status_code, 422)
        self.assertEqual(self.get("/course?student_id=2").status_code, 422)
        for no in [0, 145, -1]:
            self.assertEqual(self.get(f"/lessons/{no}").status_code, 404)
            self.assertEqual(self.check([""] * 3, no=no).status_code, 404)
        self.assertEqual(self.get("/course").json()["progress"], [])

    def test_progress_isolation_best_score_and_no_rewards(self):
        # Snapshot every existing table so a reward/history side effect is detected.
        tables = [t for t in Base.metadata.tables.values()
                  if t.name != StudentRussianProgress.__tablename__]
        def snapshot():
            with self.engine.connect() as connection:
                return {t.name: [tuple(r) for r in connection.execute(select(t))] for t in tables}
        before = snapshot()
        first = self.check(["А", "", ""]).json()["progress"]
        self.assertEqual(first, {"lesson_no": 1, "kind": "grammar",
                                 "best_score": 1, "total": 3, "attempts": 1})
        self.check(["А", "зовут", "Привет!"])
        third = self.check([""] * 3).json()["progress"]
        self.assertEqual((third["best_score"], third["attempts"]), (3, 3))
        self.assertEqual(self.get("/course", user=2).json()["progress"], [])
        other = self.check([""] * 3, user=2).json()["progress"]
        self.assertEqual((other["best_score"], other["attempts"]), (0, 1))
        self.check([""] * len(russian.LESSONS[0]["phrases"]), kind="vocabulary")
        self.check([""] * len(russian.LESSONS[1]["grammar"]["exercises"]), no=2)
        self.assertEqual(len(self.get("/course").json()["progress"]), 3)
        self.assertEqual(self.get("/course", user=2).json()["progress"], [other])
        self.assertEqual(before, snapshot())

    def test_duplicate_names_never_grant_ownership_or_auto_link(self):
        with self.sessions() as db:
            db.get(models.User, 1).full_name = "Same Name"
            db.get(models.User, 2).full_name = "Same Name"
            db.get(models.Student, 1).full_name = "Same Name"
            db.get(models.Student, 2).full_name = "Same Name"
            db.get(models.User, 7).full_name = "Same Name"
            db.commit()
        self.check(["А", "зовут", "Привет!"])
        self.assertEqual(self.get("/course", user=2).json()["progress"], [])
        for unlinked_card in (False, True):
            if unlinked_card:
                with self.sessions() as db:
                    db.get(models.Student, 1).user_id = None
                    db.get(models.Student, 2).user_id = None
                    db.commit()
            for method, path, body in [
                ("GET", "/course", None), ("GET", "/lessons/1", None),
                ("POST", "/lessons/1/check", {"kind": "grammar", "answers": [""] * 3})]:
                response = self.client.request(method, PREFIX + path, json=body,
                                               headers=self.headers(7))
                self.assertEqual(response.status_code, 403)
            with self.sessions() as db:
                self.assertEqual(db.query(StudentRussianProgress).one().attempts, 1)
                self.assertIsNone(db.query(models.Student).filter_by(user_id=7).first())
        # Defense in depth: even if the resolver returns another linked card.
        with self.sessions() as db:
            db.get(models.Student, 1).user_id = 1
            db.get(models.Student, 2).user_id = 2
            db.commit()
            other = db.get(models.Student, 2)
            with patch.object(russian, "_me", return_value=other):
                self.assertEqual(self.get("/course").status_code, 403)

    def test_all_canonical_grammar_answers(self):
        for lesson in russian.LESSONS:
            answers = [e["answer"] for e in lesson["grammar"]["exercises"]]
            result = self.check(answers, no=lesson["no"]).json()
            self.assertEqual((result["score"], result["total"]), (len(answers), len(answers)))

    def test_schema_bootstrap_creates_missing_progress_table(self):
        import common
        StudentRussianProgress.__table__.drop(self.engine)
        with self.sessions() as db:
            db.add(models.SchemaMigration(version="stamp_before_russian_course"))
            db.commit()
        with patch.object(common, "engine", self.engine),              patch.object(common, "SessionLocal", self.sessions),              patch.object(common, "_SCHEMA_OK", None),              patch.object(common, "_SCHEMA_BOOT_OK", False),              patch.object(common, "_SCHEMA_PENDING", False):
            self.assertFalse(common._schema_ready())
            common._schema_bootstrap()
            self.assertIn("student_russian_progress", inspect(self.engine).get_table_names())
            self.assertTrue(common.seal_schema())
            with self.sessions() as db:
                self.assertIsNotNone(db.query(models.SchemaMigration).filter_by(
                    version=common.schema_stamp()).first())
            self.assertTrue(common._schema_ready())

    def test_model_registration_before_schema_bootstrap(self):
        entry = (ROOT / "api/entry.py").read_text("utf-8")
        self.assertLess(entry.index("import student_russian_models"), entry.index("from main import"))
        self.assertIn("app.include_router(student_russian.router)", entry)
        self.assertIn("student_russian_progress", inspect(self.engine).get_table_names())
        import common
        self.assertIn("student_russian_progress", common._model_signature_tokens())


if __name__ == "__main__":
    unittest.main(verbosity=2)
