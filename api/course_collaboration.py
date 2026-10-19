"""Private pair artifacts, explicit consent, version-bound teacher review. No rewards.

One bounded CAS document per group/lesson; no chat, public URLs or schema change.
Mount router directly in main. No dependency on portfolio/motivation routers.
"""
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Literal
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from sqlalchemy import or_, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

import models
from auth import get_current_user
from database import get_db

BANK = json.loads(Path(__file__).with_name('student_course_practice_data.json').read_text(encoding='utf-8'))
LESSONS = {lang: {r['lesson']: r for r in rows} for lang, rows in BANK.items()}
RUBRIC = {'task': 'Vazifani bajarish', 'language': 'Tilning aniqligi', 'collaboration': 'Ikkala ishtirokchining hissasi'}
SCALE = {0: 'Dalil yo‘q', 1: 'Jiddiy qayta ishlash kerak', 2: 'Qisman bajarilgan', 3: 'Talab bajarilgan', 4: 'Aniq va to‘liq bajarilgan'}
router = APIRouter(prefix='/api/course-collaboration', tags=['course-collaboration'])


class Input(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, str_strip_whitespace=True)


class Invite(Input):
    peer_id: int = Field(gt=0)


class Expected(Input):
    expected_version: int = Field(ge=0, le=10)


class Revision(Expected):
    title: str = Field(min_length=1, max_length=100)
    text: str = Field(min_length=1, max_length=6000)
    contributions: dict[str, str]

    @field_validator('contributions')
    @classmethod
    def bounded(cls, value):
        if len(value) != 2 or any(not v.strip() or len(v) > 500 for v in value.values()):
            raise ValueError('Har bir sherikning hissasini yozing (1–500 belgi).')
        return value


class Review(Expected):
    decision: Literal['approved', 'changes_requested']
    task: int = Field(ge=0, le=4)
    language: int = Field(ge=0, le=4)
    collaboration: int = Field(ge=0, le=4)
    strength: str = Field(min_length=10, max_length=1000)
    next_step: str = Field(min_length=10, max_length=1000)
    speaking_observed: bool = False
    fluency: int | None = Field(default=None, ge=0, le=4)
    pronunciation: int | None = Field(default=None, ge=0, le=4)

    @model_validator(mode='after')
    def observed_scores(self):
        if self.speaking_observed:
            if self.fluency is None or self.pronunciation is None:
                raise ValueError('Jonli kuzatuv uchun ravonlik va talaffuz baholari kerak.')
        elif self.fluency is not None or self.pronunciation is not None:
            raise ValueError('Jonli eshitilmagan dialogga og‘zaki baho qo‘yilmaydi.')
        return self


def _now():
    return datetime.now(timezone.utc).isoformat()


def _today():
    return datetime.now(timezone(timedelta(hours=5))).date()


def _real(row):
    return not ((getattr(row, 'username', '') or '').startswith('demo.') or
                '(DEMO)' in (getattr(row, 'full_name', '') or '') or
                '(DEMO)' in (getattr(row, 'name', '') or ''))


def _actor(request: Request, response: Response, db: Session = Depends(get_db), user=Depends(get_current_user)):
    response.headers['Cache-Control'] = 'private, no-store'
    response.headers['Vary'] = 'Authorization'
    if any(k in request.query_params for k in ('student_id', 'user_id', 'demo')):
        raise HTTPException(422, 'Hisob yoki demo almashtirish mumkin emas.')
    if not user.is_active or not _real(user):
        raise HTTPException(403, 'Faol haqiqiy hisob kerak.')
    model = {'student': models.Student, 'teacher': models.Teacher}.get(user.role)
    if model is None:
        raise HTTPException(403, 'Faqat o‘quvchi yoki guruh o‘qituvchisi.')
    rows = db.query(model).filter_by(user_id=user.id).all()
    if len(rows) != 1 or not _real(rows[0]):
        raise HTTPException(403, 'Hisob yagona kartaga bog‘lanmagan.')
    row = rows[0]
    branch = db.get(models.Branch, row.branch_id) if row.branch_id else None
    if branch and branch.is_test:
        raise HTTPException(403, 'Mashq filiali haqiqiy juftlik ishiga qo‘shilmaydi.')
    if (user.role == 'student' and row.status != 'active') or (user.role == 'teacher' and not row.is_active):
        raise HTTPException(403, 'Faol hisob kerak.')
    return user.role, row


def _member(db, student, group):
    if not student or student.status != 'active' or not _real(student) or not student.user_id:
        return False
    branch = db.get(models.Branch, student.branch_id) if student.branch_id else None
    if branch and branch.is_test:
        return False
    account = db.get(models.User, student.user_id)
    if not account or not account.is_active or account.role != 'student' or not _real(account):
        return False
    # Explicit inactive/frozen link overrides the legacy primary-group field.
    link = db.query(models.StudentGroupLink).filter_by(student_id=student.id, group_id=group.id).first()
    if link:
        return bool(link.active and (link.status or 'active') == 'active' and
                    (not link.joined_date or link.joined_date <= _today()) and
                    (not link.left_date or link.left_date > _today()) and
                    (not link.activated_on or link.activated_on <= _today()))
    return student.group_id == group.id


def _group_active(group):
    return bool(group and _real(group) and not group.archived_at and
                (not group.start_date or group.start_date <= _today()) and
                (not group.end_date or group.end_date >= _today()))


def _access(db, group, actor):
    if not _group_active(group):
        return False
    branch = db.get(models.Branch, group.branch_id) if group.branch_id else None
    if not branch or branch.is_test:
        return False
    role, person = actor
    return group.teacher_id == person.id if role == 'teacher' else _member(db, person, group)


def _groups(db, actor):
    role, person = actor
    query = db.query(models.Group)
    if role == 'teacher':
        query = query.filter(models.Group.teacher_id == person.id)
    else:
        linked = db.query(models.StudentGroupLink.group_id).filter_by(student_id=person.id, active=1)
        query = query.filter(or_(models.Group.id == person.group_id, models.Group.id.in_(linked)))
    return [g for g in query.all() if _access(db, g, actor)]


def _peers(db, group):
    linked = db.query(models.StudentGroupLink.student_id).filter_by(group_id=group.id, active=1)
    return db.query(models.Student).filter(models.Student.status == 'active', or_(
        models.Student.group_id == group.id, models.Student.id.in_(linked))).all()


def _scope(group_id: int, language: Literal['en', 'de'], lesson: int = Query(ge=1, le=192),
           actor=Depends(_actor), db: Session = Depends(get_db)):
    group = db.get(models.Group, group_id)
    if not _access(db, group, actor):
        raise HTTPException(404, 'Guruh topilmadi.')
    row = LESSONS.get(language, {}).get(lesson)
    if row is None:
        raise HTTPException(404, 'Dars topilmadi.')
    return actor, group, language, lesson, row


def _load(db, context):
    _, group, language, lesson, _ = context
    key = f'course-collaboration:v1:{group.id}:{language}:{lesson}'
    old = db.query(models.IntegrationSetting.value).filter_by(key=key).scalar()
    return key, old, json.loads(old) if old else {'entries': []}


def _save(db, key, old, state):
    raw = json.dumps(state, ensure_ascii=False, separators=(',', ':'))
    if len(raw.encode('utf-8')) > 2 * 1024 * 1024:
        raise HTTPException(409, 'Guruh/dars saqlash chegarasiga yetdi.')
    try:
        if old is None:
            db.add(models.IntegrationSetting(key=key, value=raw))
            db.flush()
        else:
            result = db.execute(update(models.IntegrationSetting).where(
                models.IntegrationSetting.key == key, models.IntegrationSetting.value == old
            ).values(value=raw).execution_options(synchronize_session=False))
            if result.rowcount != 1:
                db.rollback()
                raise HTTPException(409, 'Ish o‘zgargan. Qayta yuklang.')
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, 'Ish o‘zgargan. Qayta yuklang.')


def _eligible(db, entry, group):
    return all(_member(db, db.get(models.Student, sid), group) for sid in entry['members'])


def _entry(db, context, state, entry_id):
    actor, group, *_ = context
    entry = next((e for e in state['entries'] if e['id'] == entry_id), None)
    if not entry or (actor[0] == 'student' and actor[1].id not in entry['members']) or not _eligible(db, entry, group):
        raise HTTPException(404, 'Juftlik topilmadi yoki a’zolik faol emas.')
    return entry


def _student_only(context):
    if context[0][0] != 'student':
        raise HTTPException(403, 'Bu amal o‘quvchi uchun.')
    return context[0][1].id


def _expected(entry, expected):
    if expected != len(entry['versions']):
        raise HTTPException(409, 'Yangi versiya mavjud. Qayta yuklang.')


def _name(student):
    parts = student.full_name.split()
    return parts[0] + (' ' + parts[1][0] + '.' if len(parts) > 1 else '') if parts else 'O‘quvchi'


@router.get('/groups')
def groups(actor=Depends(_actor), db: Session = Depends(get_db)):
    return {'groups': [{'id': g.id, 'name': g.name} for g in _groups(db, actor)]}


@router.get('/review-queue')
def review_queue(actor=Depends(_actor), db: Session = Depends(get_db)):
    if actor[0] != 'teacher':
        raise HTTPException(403, 'Faqat guruh o‘qituvchisi.')
    owned = {g.id: g for g in _groups(db, actor)}
    if not owned:
        return {'items': []}
    documents = db.query(models.IntegrationSetting.key, models.IntegrationSetting.value).filter(or_(
        *[models.IntegrationSetting.key.like(f'course-collaboration:v1:{gid}:%') for gid in owned])).all()
    items = []
    for key, raw in documents:
        _, _, gid, language, lesson = key.split(':')
        group = owned[int(gid)]
        for entry in json.loads(raw)['entries']:
            latest = entry['versions'][-1] if entry['versions'] else None
            if latest and latest['submitted_at'] and not latest['review'] and _eligible(db, entry, group):
                items.append({'entry_id': entry['id'], 'group_id': group.id, 'group_name': group.name,
                              'language': language, 'lesson': int(lesson), 'title': latest['title'],
                              'version': latest['number'], 'submitted_at': latest['submitted_at']})
    return {'items': sorted(items, key=lambda item: item['submitted_at'])}


@router.get('/groups/{group_id}')
def listing(context=Depends(_scope), db: Session = Depends(get_db)):
    actor, group, _, _, row = context
    state = _load(db, context)[2]
    entries = []
    for entry in state['entries']:
        if not _eligible(db, entry, group):
            continue
        if actor[0] == 'student':
            if actor[1].id in entry['members']:
                entries.append(entry)
        else:
            # Teachers see only jointly submitted versions, never unconsented drafts.
            versions = [v for v in entry['versions'] if v.get('submitted_at')]
            if versions:
                entries.append({**entry, 'versions': versions})
    peers = []
    if actor[0] == 'student':
        peers = [{'id': s.id, 'name': _name(s)} for s in _peers(db, group)
                 if s.id != actor[1].id and _member(db, s, group)]
    return {'entries': entries, 'peers': peers, 'me': actor[1].id, 'role': actor[0],
            'rubric': RUBRIC, 'scale': SCALE, 'xp': 0, 'verified_mastery': False,
            'lesson_title': row['title'],
            'prompt': next((q['prompt'] for s in row['sections'] for q in s['questions'] if q['mode'] == 'self'), row['title'])}


@router.post('/groups/{group_id}/invites', status_code=201)
def invite(body: Invite, context=Depends(_scope), db: Session = Depends(get_db)):
    sid = _student_only(context)
    peer = db.get(models.Student, body.peer_id)
    if sid == body.peer_id or not _member(db, peer, context[1]):
        raise HTTPException(404, 'Faol guruhdosh topilmadi.')
    key, old, state = _load(db, context)
    if len(state['entries']) >= 100 or sum(sid in e['members'] for e in state['entries']) >= 8:
        raise HTTPException(409, 'Bu dars uchun taklif chegarasiga yetdi.')
    if any(set(e['members']) == {sid, body.peer_id} and e['status'] != 'declined' for e in state['entries']):
        raise HTTPException(409, 'Bu sherik bilan juftlik mavjud.')
    entry = {'id': uuid4().hex, 'members': [sid, body.peer_id],
             'names': {str(s.id): _name(s) for s in (context[0][1], peer)},
             'status': 'invited', 'created_at': _now(), 'versions': [],
             'task': {'language': context[2], 'lesson': context[3], 'title': context[4]['title'],
                      'prompt': next((q['prompt'] for s in context[4]['sections'] for q in s['questions'] if q['mode'] == 'self'), context[4]['title'])}}
    state['entries'].append(entry)
    _save(db, key, old, state)
    return entry


@router.post('/groups/{group_id}/{entry_id}/respond')
def respond(entry_id: str, accept: bool, context=Depends(_scope), db: Session = Depends(get_db)):
    sid = _student_only(context)
    key, old, state = _load(db, context)
    entry = _entry(db, context, state, entry_id)
    if sid != entry['members'][1] or entry['status'] != 'invited':
        raise HTTPException(409, 'Faqat taklif qilingan sherik javob bera oladi.')
    entry['status'] = 'accepted' if accept else 'declined'
    entry['responded_at'] = _now()
    _save(db, key, old, state)
    return entry


@router.post('/groups/{group_id}/{entry_id}/versions', status_code=201)
def revise(entry_id: str, body: Revision, context=Depends(_scope), db: Session = Depends(get_db)):
    sid = _student_only(context)
    key, old, state = _load(db, context)
    entry = _entry(db, context, state, entry_id)
    _expected(entry, body.expected_version)
    if entry['status'] != 'accepted' or len(entry['versions']) >= 10:
        raise HTTPException(409, 'Qabul qilingan juftlik kerak; ko‘pi bilan 10 versiya.')
    previous = entry['versions'][-1] if entry['versions'] else None
    if previous and previous.get('submitted_at') and not previous.get('review'):
        raise HTTPException(409, 'Avval o‘qituvchi tekshiruvini kuting.')
    if set(body.contributions) != {str(s) for s in entry['members']}:
        raise HTTPException(422, 'Har ikki ishtirokchining hissasi kerak.')
    entry['versions'].append({**body.model_dump(exclude={'expected_version'}), 'number': len(entry['versions']) + 1,
                              'author': sid, 'created_at': _now(), 'consents': {}, 'submitted_at': None, 'review': None})
    _save(db, key, old, state)
    return entry


@router.post('/groups/{group_id}/{entry_id}/consent')
def consent(entry_id: str, body: Expected, context=Depends(_scope), db: Session = Depends(get_db)):
    sid = _student_only(context)
    key, old, state = _load(db, context)
    entry = _entry(db, context, state, entry_id)
    _expected(entry, body.expected_version)
    if entry['status'] != 'accepted' or not entry['versions']:
        raise HTTPException(409, 'Avval ishni saqlang.')
    version = entry['versions'][-1]
    if version['submitted_at'] or str(sid) in version['consents']:
        return entry  # duplicate network retry is idempotent
    version['consents'][str(sid)] = _now()
    if set(version['consents']) == {str(s) for s in entry['members']}:
        version['submitted_at'] = _now()
    _save(db, key, old, state)
    return entry


@router.post('/groups/{group_id}/{entry_id}/review')
def review(entry_id: str, body: Review, context=Depends(_scope), db: Session = Depends(get_db)):
    if context[0][0] != 'teacher':
        raise HTTPException(403, 'Faqat shu guruhning o‘qituvchisi.')
    key, old, state = _load(db, context)
    entry = _entry(db, context, state, entry_id)
    _expected(entry, body.expected_version)
    if not entry['versions']:
        raise HTTPException(409, 'Topshirilgan ish yo‘q.')
    version = entry['versions'][-1]
    if not version['submitted_at'] or version['review'] or set(version['consents']) != {str(s) for s in entry['members']}:
        raise HTTPException(409, 'Ikkala rozilik bilan topshirilgan, tekshirilmagan versiya kerak.')
    scores = [body.task, body.language, body.collaboration]
    if body.speaking_observed:
        scores.extend([body.fluency, body.pronunciation])
    if body.decision == 'approved' and min(scores) < 3:
        raise HTTPException(422, 'Tasdiqlash uchun har bir baholangan mezon kamida 3 bo‘lsin.')
    version['review'] = {**body.model_dump(exclude={'expected_version'}), 'version': version['number'],
                         'teacher_id': context[0][1].id, 'created_at': _now(),
                         'observed_at': _now() if body.speaking_observed else None,
                         'observed_by': context[0][1].id if body.speaking_observed else None}
    _save(db, key, old, state)
    # A student may supersede an unsubmitted draft. Never expose those historical
    # drafts through the mutation response, either.
    return {**entry, 'versions': [v for v in entry['versions'] if v['submitted_at']]}
