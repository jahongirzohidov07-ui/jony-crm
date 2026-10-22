import ast
import sys
from pathlib import Path
from datetime import datetime
import unittest

# Execute the production grading functions without booting entry.py's application.
# 2026-10-22: _pt_sec_grade "juda tez" uchun _pt_elapsed_ms va placement_guard
# (_PG) ni ishlatadi va (ball, max, kechikdi, bilmayman, juda tez) qaytaradi.
sys.path.insert(0, 'api')
import placement_guard  # noqa: E402
tree = ast.parse(Path('api/entry.py').read_text(encoding='utf-8'))
names = {'_pt_choice_matches', '_pt_sec_grade', '_pt_elapsed_ms'}
scope = {'_pt_dt': datetime, '_pt_now': datetime.utcnow,
         '_pt_sec_secs': lambda *args: 60, '_PT_GRACE': 5, '_PG': placement_guard}
exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in names], type_ignores=[]), 'api/entry.py', 'exec'), scope)

class PlacementUnknown(unittest.TestCase):
    def test_indices_never_default_or_wrap(self):
        match = scope['_pt_choice_matches']
        for invalid in (-1, -2, None, '', '0', '-1', False, True, 0.0, 4):
            self.assertFalse(match([0, 1, 2, 3], invalid, 3), repr(invalid))
            self.assertFalse(match([0, 1, 2, 3], invalid, 0), repr(invalid))
        for i in range(4):
            self.assertTrue(match([0, 1, 2, 3], i, i))

    def test_each_public_section_unknown_and_missing(self):
        grade = scope['_pt_sec_grade']
        opts = ['one', 'two', 'three', 'four']
        fixtures = [
            ('grammar', {'a':3,'q':'?','opts':opts}, {'o':[0,1,2,3]}, 'choice', 3, 1),
            ('listening', {'a':3,'q':'?','opts':opts}, {'o':[0,1,2,3]}, 'choice', 3, 1),
            ('reading', {'text':'A short text.','qs':[{'a':3,'q':'?','opts':opts},{'a':3,'q':'?','opts':opts}]},
             {'o':[[0,1,2,3]]*2}, 'picks', [3,3], 2),
            ('vocab', {'defs':[['a',5],['b',5],['c',5]],'words':['w0','w1','w2','w3','w4','w5']},
             {'d':[0,1,2], 'w':list(range(6))}, 'picks', [5]*3, 3),
        ]
        for sec,item,cur,key,right,maximum in fixtures:
            unknown = -1 if key == 'choice' else [-1]*len(right)
            # "Bilmayman" (-1): xato va idk sifatida sanaladi, hech qachon to'g'ri emas
            self.assertEqual(grade(sec,item,cur,{key:unknown}), (0,maximum,False,maximum,0), sec)
            self.assertEqual(grade(sec,item,cur,{}), (0,maximum,False,0,0), sec)
            # savol berilgan vaqt yo'q (eski sessiya) — "juda tez" qo'llanmaydi
            self.assertEqual(grade(sec,item,cur,{key:right}), (maximum,maximum,False,0,0), sec)
            # hozirgina berilgan savolga darrov to'g'ri javob — juda tez, ball 0
            fresh = dict(cur, sent=datetime.utcnow().isoformat())
            self.assertEqual(grade(sec,item,fresh,{key:right}), (0,maximum,False,0,maximum), sec)
            # darrov "Bilmayman" — juda tez emas, faqat idk
            self.assertEqual(grade(sec,item,fresh,{key:unknown}), (0,maximum,False,maximum,0), sec)

    def test_student_unknown_cannot_match_answer(self):
        tree = ast.parse(Path('api/level_test.py').read_text(encoding='utf-8'))
        fn = next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='lt_answer')
        grading = [n for n in fn.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id in ('given','correct') for t in n.targets)]
        code = compile(ast.Module(body=grading,type_ignores=[]),'api/level_test.py','exec')
        for expected in ('-1','', 'right'):
            for answer in (-1, '-1', None, ''):
                env={'payload':{'answer':answer},'cur':{'answer':expected}}
                exec(code,env)
                self.assertFalse(env['correct'])
        env={'payload':{'answer':'RIGHT'},'cur':{'answer':'right'}}
        exec(code,env)
        self.assertTrue(env['correct'])

unittest.main()
