"""Teacher Russian localization coverage and preservation of canonical student content."""
import argparse
import json
import re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser();parser.add_argument('--pdf',action='store_true');args=parser.parse_args()
source=[];translations=[]
for part in range(1,5):
 source.extend(json.loads((ROOT/f'src/data/russian/part-{part}.json').read_text('utf-8')))
 overlay=json.loads((ROOT/f'src/data/russian/teacher-ru-{part}.json').read_text('utf-8'))
 assert len(overlay)==36,(part,len(overlay))
 translations.extend(overlay)
assert [t['no'] for t in translations]==list(range(1,145))
assert len({t['title'] for t in translations})==144
strings=0
for base,t in zip(source,translations):
 n=base['no']
 assert set(t)=={'no','title','objective','grammar','questions','roleplay','teacherTip','homework','exit'},n
 assert set(t['grammar'])=={'title','rule','exercises'},n
 assert len(t['grammar']['exercises'])==len(base['grammar']['exercises'])==3
 assert len(t['questions'])==len(base['questions'])==3
 assert len(t['homework'])==len(base['homework'])==3
 assert set(t['roleplay'])==set(base['roleplay'])=={'a','b','twist','success'}
 fields=[(k,t[k]) for k in ('title','objective','teacherTip','exit')]
 fields += [('grammar.'+k,t['grammar'][k]) for k in ('title','rule')]
 fields += [('roleplay.'+k,v) for k,v in t['roleplay'].items()]
 fields += [('homework',v) for v in t['homework']]
 for e in t['grammar']['exercises']:
  assert set(e)=={'prompt','explanation'},n
  fields.extend(e.items())
 for q in t['questions']:
  assert set(q)=={'prompt'},n
  fields.extend(q.items())
 for field,value in fields:
  assert isinstance(value,str) and value.strip(),(n,field)
  assert re.search('[А-Яа-яЁё]',value),(n,field,value)
  assert '\ufffd' not in value,(n,field)
  strings+=1
 if n%12==0 and n<144:
  assert '14/20' in t['teacherTip'],(n,'monthly score')
 if n==144:
  for fraction in ('40/60','8/15','2/3'):
   assert fraction in t['teacherTip'],(n,fraction)
  assert '40/60' in t['exit']
 # Overlay may translate prompts/explanations but cannot replace canonical answers or bilingual examples.
 g={**base['grammar'],**t['grammar'],'exercises':[{**q,**tr} for q,tr in zip(base['grammar']['exercises'],t['grammar']['exercises'])]}
 assert [q['answer'] for q in g['exercises']]==[q['answer'] for q in base['grammar']['exercises']]
 assert g['examples']==base['grammar']['examples']
# Student runtime export remains source-based, not teacher-only Russian instructions.
export=json.loads((ROOT/'api/student_russian_data.json').read_text('utf-8'))
for base,student in zip(source,export):
 for key in ('title','objective','grammar','phrases','dialog','questions','homework','exit','roleplay'):
  assert student[key]==base[key],(base['no'],'student regression',key)
ui=(ROOT/'src/pages/RussianPlans.tsx').read_text('utf-8')
assert "../lib/russianTeacher" in ui and 'locale="ru"' in ui
for label in ('Ustoz rejasi','Uyga vazifa','Darsni qanday','Oldingi dars','Keyingi dars','Namunaviy javob'):
 assert label not in ui,label
if args.pdf:
 import pypdfium2 as pdfium
 paths=[ROOT/'public/russian/jony-russian-course-map.pdf']
 paths += [ROOT/f'public/russian/jony-russian-month-{m}-{kind}.pdf' for m in range(1,13) for kind in ('teacher','workbook')]
 pages=0
 for path in paths:
  doc=pdfium.PdfDocument(path);pages+=len(doc)
  text='\n'.join(page.get_textpage().get_text_range() for page in doc)
  assert re.search('[А-Яа-яЁё]',text),path
  for old in ('Ustoz qo‘llanmasi','Uyga vazifa','USTOZ VAZIFASI','Chiqish tekshiruvi','Kurs xaritasi'):
   assert old not in text,(path,old)
  for number,page in enumerate(doc):
   width,height=page.get_size();tp=page.get_textpage()
   for i in range(tp.count_rects()):
    x0,y0,x1,y1=tp.get_rect(i)
    assert x0>=-1 and y0>=-1 and x1<=width+1 and y1<=height+1,(path,number,(x0,y0,x1,y1))
   tp.close();page.close()
  doc.close()
 print(f'PASS: 25 Russian PDF files, {pages} pages; Cyrillic text and page bounds')
print(f'PASS: 144 teacher lessons, {strings} Russian instructional fields, original student content and answer keys preserved')
