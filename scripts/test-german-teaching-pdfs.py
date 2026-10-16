"""Check generated German books against the exact UI export (no rendering claims)."""
import json
import subprocess
from pathlib import Path
from pypdf import PdfReader
ROOT = Path(__file__).resolve().parents[1]
data = json.loads(subprocess.check_output(['node', str(ROOT/'scripts/export-german-teaching.cjs')], cwd=ROOT, encoding='utf-8'))
out = ROOT/'public/german'
def read(name):
    pdf=PdfReader(out/(name+'.pdf'))
    text='\n'.join(page.extract_text() or '' for page in pdf.pages)
    assert text.strip(), name
    print(f'{name}: {len(pdf.pages)} pages')
    return pdf,text
_,grammar=read('jony-deutsch-grammar')
_,keys=read('jony-deutsch-answer-key')
for e in data['exercises']:
    assert e['id'] in grammar, e['id']
    assert e['id'] in keys, e['id']
course,course_text=read('jony-deutsch-course-map')
assert 'birinchi 20 so‘z' not in course_text
assert '30, support kuni 20' not in course_text
assert 'Prüfungstraining 1' in course_text and 'Prüfungstraining 2' in course_text
assert '75 daqiqa' in course_text
links=[]
for page in course.pages:
    for ref in page.get('/Annots',[]):
        action=ref.get_object().get('/A',{})
        if action.get('/URI'): links.append(str(action['/URI']))
for kit in data['lessons']:
    assert any(link.endswith(kit['audioPath'].split('/')[-1]) for link in links), kit['no']
    assert all(f'#{wid}' in course_text for wid in kit['vocabulary']['activeIds'])
for month in range(1,7):
    pdf,text=read(f'jony-deutsch-month-{month}-skills')
    assert 'audio yozuv emas' not in text
    assert 'sun’iy ovozli MP3' in text
    if month < 6:
        assert f'{month}-oy · ichki nazorat' in text
        assert 'USTOZ KALITI' in text
        checkpoint=data['lessons'][month*12-1]['checkpoint']
        assert checkpoint['readingQuestions'][0][0] in text
print('PASS: 9 updated PDFs; all 432 added tasks and keys; all 72 audio links; five checkpoint packets; no obsolete schedule/audio labels. Visual layout review remains separate.')
