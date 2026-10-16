"""Run directly: python api/test_student_course_practice.py. No live DB access."""
import os
import sys
import unittest
from pathlib import Path

# Set before any application imports; all persistence stays in memory.
os.environ["DATABASE_URL"] = "sqlite://"
sys.path.insert(0, str(Path(__file__).resolve().parent))
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from types import SimpleNamespace

import models
import student_course_practice as practice
from auth import get_current_user
from database import get_db


class CoursePracticeTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
        # Only these tables are required; SQLite foreign keys are off by default.
        models.Student.__table__.create(self.engine)
        models.SkillAttempt.__table__.create(self.engine)
        self.db = sessionmaker(bind=self.engine)()
        self.db.add_all([models.Student(id=1, full_name="One", user_id=11, status="active"),
                         models.Student(id=2, full_name="Two", user_id=22, status="active"),
                         models.Student(id=3, full_name="Unlinked", status="active")])
        self.db.commit()
        self.user = SimpleNamespace(id=11, role="student", full_name="One", is_active=1)
        self.app = FastAPI()
        self.app.include_router(practice.router)
        self.app.dependency_overrides[get_db] = lambda: self.db
        self.app.dependency_overrides[get_current_user] = lambda: self.user
        self.client = TestClient(self.app)

    def tearDown(self):
        self.client.close()
        self.db.close()
        self.engine.dispose()

    def post(self, qid, answer="My own answer", language="en", lesson=1, **extra):
        return self.client.post("/api/student/course-practice/answer", json=dict(
            language=language, lesson=lesson, question_id=qid, answer=answer, **extra))

    def test_full_bank_projection_and_coverage(self):
        for language, count in [("en",192),("de",72)]:
            listing = self.client.get("/api/student/course-practice", params={"language":language}).json()
            self.assertEqual(len(listing["lessons"]), count)
            for row in practice.BANK[language]:
                public = practice.lesson_detail(row["lesson"], language, self.db.get(models.Student,1))
                for section in public["sections"]:
                    self.assertNotIn("transcript",section)
                    if section["skill"] == "listening":
                        self.assertNotIn("text",section)
                    if "text" in section:
                        self.assertIsInstance(section["text"],str)
                    for question in section["questions"]:
                        self.assertLessEqual(set(question), {"id","prompt","mode","options"})
                self.assertEqual(listing["lessons"][row["lesson"]-1]["question_count"],
                                 sum(len(s["questions"]) for s in row["sections"]))
        en = practice.BANK["en"]
        self.assertEqual(sum(len([q for q in s["questions"] if q["id"].split(":")[-1].startswith(("r-","l-"))])
                             for l in en for s in l["sections"]),1536)
        self.assertEqual(sum(s["id"]=="homework" for l in en for s in l["sections"]),32)
        deids = {q["id"].split(":")[-1] for l in practice.BANK["de"] for s in l["sections"] for q in s["questions"]
                 if q["id"].endswith(("-production","-correction","-transfer"))}
        self.assertEqual(len(deids),432)

    def test_feedback_and_distinct_persisted_progress(self):
        q = practice.BANK["en"][0]["sections"][0]["questions"][0]
        for value in [q["expected"][0], q["expected"][0], "wrong"]:
            self.assertEqual(self.post(q["id"],value).status_code,200)
        selfq = next(q for s in practice.BANK["en"][0]["sections"] for q in s["questions"] if q["mode"]=="self")
        result = self.post(selfq["id"]).json()
        self.assertIsNone(result["correct"])
        self.assertTrue(result["saved"])
        self.assertIn("criteria",result)
        persisted = self.db.query(models.SkillAttempt).filter_by(ref=practice._ref(selfq["id"])).one()
        self.assertEqual(persisted.correct,0)
        self.assertTrue(persisted.skill.startswith("course-practice:en:"))
        progress = self.client.get("/api/student/course-practice?language=en").json()["lessons"][0]
        self.assertEqual(progress["submitted_count"],2)
        self.assertEqual(progress["correct_count"],1)
        self.assertFalse(progress["completed"])
        self.user = SimpleNamespace(id=22,role="student",full_name="Two",is_active=1)
        self.assertEqual(self.client.get("/api/student/course-practice?language=en").json()["lessons"][0]["submitted_count"],0)
        self.assertEqual(self.db.query(models.SkillAttempt).filter_by(student_id=2).count(),0)

    def test_transcript_only_on_listening_answer(self):
        row = practice.BANK["en"][0]
        for section in row["sections"]:
            if not section["questions"]: continue
            result = self.post(section["questions"][0]["id"]).json()
            self.assertEqual("transcript" in result,section["skill"]=="listening")
            if "transcript" in result: self.assertEqual(result["transcript"],section["transcript"])

    def test_validation_and_language_isolation(self):
        qid = practice.BANK["en"][0]["sections"][0]["questions"][0]["id"]
        for kwargs in [dict(answer=" "),dict(answer="x"*6001),dict(student_id=2),
                       dict(language="fr"),dict(lesson=True),dict(lesson=0),dict(answer=123)]:
            self.assertEqual(self.post(qid,**kwargs).status_code,422)
        self.assertEqual(self.post(qid,language="de").status_code,404)
        self.assertEqual(self.post(qid,lesson=2).status_code,404)
        self.assertEqual(self.post("missing").status_code,404)
        self.assertEqual(self.client.get("/api/student/course-practice/73?language=de").status_code,404)
        self.assertEqual(self.client.get("/api/student/course-practice?language=fr").status_code,422)
        self.assertEqual(self.client.get("/api/student/course-practice?language=en&student_id=2").status_code,422)
        self.assertEqual(self.db.query(models.SkillAttempt).count(),0)

    def test_real_auth_scope_no_name_autolink(self):
        for user in [SimpleNamespace(id=33,role="student",full_name="Unlinked",is_active=1),
                     SimpleNamespace(id=44,role="teacher",full_name="One",is_active=1)]:
            self.user=user
            self.assertEqual(self.client.get("/api/student/course-practice?language=en").status_code,403)
        self.assertIsNone(self.db.get(models.Student,3).user_id)
        self.user=SimpleNamespace(id=11,role="student",full_name="One",is_active=1)
        self.db.get(models.Student,1).status="frozen"
        self.db.commit()
        self.assertEqual(self.client.get("/api/student/course-practice/1?language=en").status_code,403)
        self.app.dependency_overrides.pop(get_current_user)
        self.assertIn(self.client.get("/api/student/course-practice?language=en").status_code,[401,403])

    def test_german_case_sensitive_and_self_production(self):
        q=next(q for s in practice.BANK["de"][0]["sections"] for q in s["questions"] if q["id"].endswith("g001-q1"))
        self.assertFalse(self.post(q["id"],"buch","de").json()["correct"])
        self.assertTrue(self.post(q["id"],"Buch","de").json()["correct"])
        result=self.post("de:1:g001-production","Different valid production","de").json()
        self.assertIsNone(result["correct"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
