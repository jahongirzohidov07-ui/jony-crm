"""Validate published course data and linked PDFs without production writes."""
import json
import re
from pathlib import Path

root=Path(__file__).resolve().parents[1]
lessons=sum([json.loads((root/f'src/data/russian/part-{i}.json').read_text(encoding='utf-8')) for i in range(1,5)],[])
assert [l['no'] for l in lessons]==list(range(1,145)), '144 ordered, unique lessons required'
assert len({l['title'] for l in lessons})==144, 'Duplicate lesson titles'
for l in lessons:
    n=l['no']
    assert l['month']==(n-1)//12+1 and l['week']==(n-1)//3+1, n
    for field in ('title','objective','teacherTip','exit'):
        assert isinstance(l[field],str) and len(l[field].strip())>12, (n,field)
    if n%12==0 and n<144:
        assert '14/20' in l['teacherTip'], (n,'monthly rubric')
        assert not re.search(r'7/10|9/12|12/16',l['exit']), (n,'inconsistent exit score')
    if n==144: assert '40/60' in l['teacherTip'] and '40/60' in l['exit']
    g=l['grammar']
    assert len(g['examples'])==2 and len(g['exercises'])==3, n
    assert len(l['phrases'])==8 and len(l['dialog']) in (6,8), n
    assert len(l['questions'])==3 and len(l['homework'])==3, n
    for e in g['examples']+l['phrases']+l['dialog']:
        assert re.search('[А-Яа-яЁё]',e['ru']) and len(e['uz'])>1, (n,e)
    assert {e['speaker'] for e in l['dialog']}=={'A','B'}, n
    for q in g['exercises']:
        assert all(isinstance(q[k],str) and q[k].strip() for k in ('prompt','answer','explanation')), (n,q)
    for q in l['questions']:
        assert q['prompt'].strip() and q['answer'].strip(), n
    for key in ('a','b','twist','success'):
        assert len(l['roleplay'][key])>20, (n,key)
    for h in l['homework']: assert isinstance(h,str) and len(h)>15, (n,h)
for m in range(1,13):
    assert len([l for l in lessons if l['month']==m])==12, m
    for kind in ('teacher','workbook'):
        f=root/f'public/russian/jony-russian-month-{m}-{kind}.pdf'
        assert f.is_file() and f.stat().st_size>20000, f
assert (root/'public/russian/jony-russian-course-map.pdf').is_file()
ui=(root/'src/pages/RussianPlans.tsx').read_text(encoding='utf-8')
assert 'russian-placement' in ui and 'Sintetik ovoz' in ui
assert 'getVoices()' in ui and "startsWith('ru')" in ui
assert 'RussianPlans' in (root/'src/pages/LessonPlans.tsx').read_text(encoding='utf-8')
print('PASS: 144 lessons, 12 months, 432 grammar checks, 432 comprehension prompts, 1152 phrase slots, 25 PDF files and course routing')
