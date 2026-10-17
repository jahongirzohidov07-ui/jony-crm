"""Identity regression tests; isolated memory DB, no production writes."""
import os
os.environ["DATABASE_URL"] = "sqlite://"
import unittest
from types import SimpleNamespace
from unittest.mock import patch
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi import HTTPException
from starlette.requests import Request
import models, common, student_app, auth_users, schemas

class IdentityTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite://")
        models.Student.__table__.create(self.engine)
        models.User.__table__.create(self.engine)
        self.db = sessionmaker(bind=self.engine)()
        self.user = models.User(id=10, username="student-test", full_name="Same Name", role="student", password_hash="test", is_active=1)
        self.db.add(self.user)
        self.db.commit()
    def tearDown(self):
        self.db.close()
        self.engine.dispose()
    def card(self, id, uid=None, name="Same Name", phone="998900001111", status="active"):
        s=models.Student(id=id, full_name=name, phone=phone, user_id=uid, status=status)
        self.db.add(s); self.db.commit(); return s
    def test_unlinked_same_name_is_not_claimed(self):
        s=self.card(1)
        with patch.object(self.db,"commit",side_effect=AssertionError("lookup wrote")):
            self.assertIsNone(common._student_of_user(self.db,self.user))
        self.assertIsNone(s.user_id)
    def test_same_name_owned_by_another_account_denied(self):
        self.card(1,20)
        self.assertIsNone(common._student_of_user(self.db,self.user))
        with self.assertRaises(HTTPException) as caught: student_app._me(self.db,self.user)
        self.assertEqual(caught.exception.status_code,403)
    def test_explicit_link_wins_despite_renaming_and_shared_phone(self):
        self.card(1,20)
        own=self.card(2,10,"Renamed Student")
        self.assertEqual(student_app._me(self.db,self.user).id,own.id)
    def test_duplicate_links_fail_closed_even_if_one_archived(self):
        self.card(1,10); self.card(2,10,status="archived")
        with self.assertRaises(HTTPException) as caught: common._student_of_user(self.db,self.user)
        self.assertEqual(caught.exception.status_code,403)
    def test_missing_user_id_never_matches_unlinked_cards(self):
        self.card(1)
        self.assertIsNone(common._student_of_user(self.db,SimpleNamespace(id=None)))
        self.assertIsNone(common._student_of_user(self.db,None))
    def test_lookup_does_not_flush_pending_changes(self):
        self.card(1,10)
        self.db.add(models.Student(id=2,full_name="Pending",status="active"))
        with patch.object(self.db,"flush",side_effect=AssertionError("lookup flushed")):
            self.assertEqual(common._student_of_user(self.db,self.user).id,1)
        self.db.rollback()
    def test_status_guard_still_blocks_frozen(self):
        self.card(1,10,status="frozen")
        with self.assertRaises(HTTPException) as caught: student_app._me(self.db,self.user)
        self.assertEqual(caught.exception.status_code,403)
    def test_login_rejects_unlinked_and_ambiguous_without_issuing_token(self):
        request=Request({"type":"http","headers":[],"client":("127.0.0.1",123)})
        payload=schemas.LoginRequest(username=self.user.username,password="test")
        self.card(1,20)
        for duplicate in [False,True]:
            if duplicate:
                self.card(2,10);self.card(3,10)
            with patch.object(auth_users,"_login_guard"), patch.object(auth_users,"verify_password",return_value=True), patch.object(auth_users,"create_access_token") as token:
                with self.assertRaises(HTTPException) as caught: auth_users.login(payload,request,self.db)
                self.assertEqual(caught.exception.status_code,403)
                token.assert_not_called()

if __name__ == "__main__": unittest.main(verbosity=2)
