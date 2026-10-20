"""Weekly journey -> canonical portfolio persistence; isolated SQLite, no network."""
import json
import unittest
from pathlib import Path
import test_course_portfolio as existing


class WeeklyMissionTests(unittest.TestCase):
    setUp = existing.PortfolioTests.setUp
    tearDown = existing.PortfolioTests.tearDown
    url = existing.PortfolioTests.url
    body = existing.PortfolioTests.body

    def test_all_week_end_choices_match_canonical_and_stay_scoped(self):
        canonical = json.loads(Path(__file__).with_name('course_weekly_missions.json').read_text(encoding='utf-8'))
        for language, missions in canonical.items():
            for mission in missions:
                with self.subTest(language=language, week=mission['week']):
                    listing = self.client.get(self.url(language=language, lesson=mission['lesson'])).json()
                    selected = listing['missions'][0]
                    for key in ('id', 'title', 'prompt', 'output', 'criteria', 'suggested_type', 'week', 'lesson'):
                        self.assertEqual(selected[key], mission[key])
                    previous = self.client.get(self.url(language=language, lesson=mission['lesson']-1)).json()
                    self.assertNotIn(mission['id'], [m['id'] for m in previous['missions']])

    def test_saved_output_reopens_with_same_mission_and_no_mastery_or_xp(self):
        for language, lesson in [('en',6), ('en',192), ('de',3), ('de',72)]:
            listing_url = self.url(language=language, lesson=lesson)
            mission = self.client.get(listing_url).json()['missions'][0]
            response = self.client.post(listing_url, json=self.body(title=mission['title'], type=mission['suggested_type'], text='My own practice output', mission_id=mission['id']))
            self.assertEqual(response.status_code, 201, response.text)
            entry = response.json()
            saved_url = self.url(entry['id'], language=language, lesson=lesson)
            restored = self.client.get(saved_url).json()
            self.assertEqual(restored['mission'], entry['mission'])
            self.assertEqual(restored['mission']['criteria'], mission['criteria'])
            self.assertEqual(restored['versions'][0]['mission_id'], mission['id'])
            self.assertEqual(restored['mission_evidence']['status'], 'artifact_saved')
            updated = self.client.put(saved_url, json=self.body(title=mission['title'], expected_version=1, text='My revised practice output'))
            self.assertEqual(updated.status_code, 200, updated.text)
            self.assertEqual(updated.json()['mission']['id'], mission['id'])
            bad = self.client.post(self.url(language=language, lesson=lesson-1), json=self.body(mission_id=mission['id']))
            self.assertEqual(bad.status_code, 422)
        self.assertEqual(self.db.query(existing.models.SkillAttempt).count(), 0)
        self.assertEqual(self.db.query(existing.models.XpTransaction).count(), 0)


if __name__ == '__main__':
    unittest.main()
