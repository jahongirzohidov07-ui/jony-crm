"""Read-only reward guidance. Eligibility is never evidence of payment."""
from datetime import date, timedelta

from sqlalchemy import func

import models
import roles

BADGE_METRICS = {
    'vocab': ('vocabulary', 'correct_answers'),
    'xp': ('xp', 'xp'),
    'streak': ('streak', 'days'),
    'grammar_topics': ('grammar', 'topics'),
    'lessons': ('attendance', 'lessons'),
    'exams': ('exams', 'exams'),
}


def _source(id, title, description, coins, have, target, unit, status,
            href=None, action_label=None, award_mode='automatic'):
    return dict(id=id, title=title, description=description, coins=coins,
                have=have, target=target, unit=unit, status=status,
                award_mode=award_mode, href=href, action_label=action_label)


def reward_path(db, student, streak):
    """Call inside no_autoflush; uses only SELECTs, no award helpers."""
    sid = student.id
    entries = db.query(models.CoinEntry).filter(
        models.CoinEntry.student_id == sid,
        models.CoinEntry.amount > 0).all()
    last = db.query(func.max(models.VocabAttempt.date)).filter(
        models.VocabAttempt.student_id == sid).scalar()
    tag = f'[{(last - timedelta(days=streak - 1)).isoformat()}]' if last and streak else None
    sources = []
    for days, coins in roles.STREAK_REWARDS:
        paid = tag and any(e.source == 'streak' and e.ref_id == days
                           and tag in (e.note or '') for e in entries)
        sources.append(_source(
            f'streak:{days}', f'{days} kunlik lug\'at mashqi',
            'Har uzluksiz lug\'at mashqi zanjirida bir marta. '
            'Mos sahifa ochilganda tizim mukofotni hisoblaydi.',
            coins, min(streak, days), days, 'days',
            'awarded' if paid else 'eligible' if streak >= days else 'in_progress',
            '/student/vocab', 'Lug\'at mashqi'))

    # Match _recalc_gamification: sum ALL transactions, including reversals.
    xp = max(0, float(db.query(func.coalesce(func.sum(models.XpTransaction.amount), 0))
                     .filter(models.XpTransaction.student_id == sid).scalar()))
    history = {h.to_league_id for h in db.query(models.StudentLeagueHistory)
               .filter(models.StudentLeagueHistory.student_id == sid)}
    leagues = db.query(models.XpLeague).filter(
        models.XpLeague.is_active == 1).order_by(models.XpLeague.rank).all()
    eligible = [lg for lg in leagues if xp >= float(lg.minimum_xp or 0)]
    reached_rank = max([lg.rank or 0 for lg in eligible]
                       + [lg.rank or 0 for lg in leagues if lg.id in history] + [0])
    for league in leagues:
        if not (league.reward_coin or 0) > 0:
            continue
        target = float(league.minimum_xp or 0)
        # League coin entries have no stable league FK/ref_id. A note/name
        # match or promotion row is not sufficient to assert payment.
        status = ('untracked' if league.id in history or (league.rank or 0) < reached_rank else
                  'eligible' if xp >= target else 'in_progress')
        sources.append(_source(
            f'league:{league.key}', f'{league.name} ligasi',
            'Liga ko\'tarilishida avtomatik mukofot. O\'tkazib yuborilgan '
            'ligalar uchun alohida mukofot va\'da qilinmaydi. '
            'Liga tarixining o\'zi coin to\'langanini tasdiqlamaydi.',
            int(league.reward_coin), min(xp, target), target, 'xp', status,
            '/student/leagues', 'Ligalarni ko\'rish'))
        sources[-1]['practice_href'] = '/student/vocab'

    today = roles.local_today()
    week = today - timedelta(days=today.weekday() + 7)
    ref = int(week.strftime('%Y%m%d'))
    if week >= date(2026, 8, 31):
        paid = any(e.source == 'rank' and e.ref_id == ref for e in entries)
        sources.append(_source(
            f'rank:{ref}', 'Haftalik reyting g\'olibi',
            f'{week.isoformat()} haftasida umumiy XP reytingining birinchi '
            'o\'rni. Tugagan hafta mukofoti reyting ochilganda hisoblanadi. '
            'G\'oliblik bu sahifada qayta hisoblanmaydi.',
            roles.RANK_PRIZE_COIN, None, None, 'rank',
            'awarded' if paid else 'untracked',
            '/student/leaderboard', 'Reytingni ko\'rish'))

    # Reuse only pure/read-only flag and readiness helpers. /me and
    # _award_bands can write, and must never be called by this GET.
    import wordbank as wb
    flag = wb.flag_value(db)
    if flag == wb.ALL or student.branch_id in flag:
        ready = wb._ready_bands(db)
        totals = dict(db.query(wb.W.band, func.count(wb.W.id))
                      .filter(wb.W.status == 'active').group_by(wb.W.band))
        known = dict(db.query(wb.W.band, func.count(wb.SW.word_id))
                     .join(wb.SW, wb.SW.word_id == wb.W.id)
                     .filter(wb.SW.student_id == sid, wb.SW.known == 1,
                             wb.W.status == 'active').group_by(wb.W.band))
        awards = {a.band for a in db.query(wb.BA).filter(wb.BA.student_id == sid)}
        for band in sorted(ready):
            if not 1 <= band <= wb.WC.BANDS or not totals.get(band):
                continue
            target, have = totals[band], known.get(band, 0)
            paid = any(e.source == wb.COIN_SOURCE and e.ref_id == band for e in entries)
            status = ('awarded' if paid else 'untracked' if band in awards else
                      'eligible' if have >= target else 'in_progress')
            sources.append(_source(
                f'wordbank:{band}', f'Common {band}000',
                'Darajadagi barcha faol so\'zlar tasdiqlanganda bir marta. '
                'Oddiy javoblar soni tasdiqlangan so\'zlar soni emas.',
                wb.WC.coins_for_band(band), have, target, 'verified_words', status,
                '/student/words', 'So\'z bilish'))

    sources.append(_source(
        'manual', 'Xodim belgilaydigan mukofot',
        'Tanlov yoki tadbir uchun vakolatli xodim coin belgilashi mumkin. '
        'Miqdor kafolatlanmagan; bu ariza yuborilgani yoki tasdiq kutilayotganini anglatmaydi.',
        None, None, None, 'staff_decision', 'manual_review', award_mode='staff'))
    return {'student_id': sid, 'sources': sources,
            'note': 'Shart bajarilgani coin berilganini anglatmaydi. '
                    'Coin berilgani faqat coin jurnalidagi yozuv bilan tasdiqlanadi. '
                    'Tarix bilan bog‘lanmagan mukofotni coin tarixidan tekshiring. '
                    'Bu sahifa coin bermaydi va ariza yubormaydi.'}


STREAK_STATUS_LABELS = {
    'in_progress': 'Mashqni davom ettiring',
    'eligible': 'Shart bajarilgan — coin yozuvi hali tasdiqlanmagan',
    'awarded': 'Coin berilgan',
}


def streak_reward_statuses(db, student_id, streak):
    """Current-run evidence, queried after the existing achievement award call."""
    last = db.query(func.max(models.VocabAttempt.date)).filter(
        models.VocabAttempt.student_id == student_id).scalar()
    tag = f'[{(last - timedelta(days=streak - 1)).isoformat()}]' if last and streak else None
    entries = db.query(models.CoinEntry).filter(
        models.CoinEntry.student_id == student_id,
        models.CoinEntry.source == 'streak', models.CoinEntry.amount > 0).all()
    result = {}
    for days, _ in roles.STREAK_REWARDS:
        paid = tag and any(e.ref_id == days and tag in (e.note or '') for e in entries)
        status = 'awarded' if paid else 'eligible' if streak >= days else 'in_progress'
        result[days] = {'status': status, 'status_label': STREAK_STATUS_LABELS[status],
                        'award_mode': 'automatic'}
    return result
