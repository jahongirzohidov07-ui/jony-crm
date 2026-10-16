"""Build printable reviewed materials from the same course export as the UI.
Run node scripts/test-intensive.cjs --export first. Requires reportlab.
"""
from pathlib import Path
from xml.sax.saxutils import escape
import json, re, random, argparse, subprocess
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'public/intensive'
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--sections',nargs='+',choices=['teacher','vocabulary','grammar'],default=['teacher','vocabulary','grammar'])
SECTIONS=parser.parse_args().sections
D=({'words':json.loads((ROOT/'src/data/intensive-vocabulary.json').read_text(encoding='utf-8'))} if SECTIONS==['teacher'] else json.loads((OUT/'course-export.json').read_text(encoding='utf-8')))
GUIDANCE=json.loads((ROOT/'src/data/intensive-lesson-guidance.json').read_text(encoding='utf-8'))
NOTES=json.loads((ROOT/'src/data/intensive-teacher-notes.json').read_text(encoding='utf-8'))
for name,file in [('Jony','arial.ttf'),('JonyBold','arialbd.ttf')]:pdfmetrics.registerFont(TTFont(name,'C:/Windows/Fonts/'+file))
pdfmetrics.registerFontFamily('Jony',normal='Jony',bold='JonyBold')
NAVY=colors.HexColor('#10213B');BLUE=colors.HexColor('#2162E8');PALE=colors.HexColor('#F4F7FB');LINE=colors.HexColor('#DFE6F0')
styles={k:ParagraphStyle(k,fontName='JonyBold' if bold else 'Jony',fontSize=size,leading=size*1.35,textColor=color,spaceAfter=after) for k,size,bold,color,after in [('title',27,True,NAVY,15),('h',15,True,NAVY,9),('sub',11,True,BLUE,6),('p',10,False,NAVY,7),('small',8,False,NAVY,4),('cell',8.5,False,NAVY,0)]}
def p(text,style='p'):return Paragraph(escape(str(text)).replace('\n','<br/>'),styles[style])
def frame(c,doc):
    w,h=doc.pagesize;c.saveState()
    c.drawImage(str(ROOT/'src/assets/brand-icon.png'),36,h-43,21,21,mask='auto')
    c.setFont('JonyBold',10);c.setFillColor(NAVY);c.drawString(65,h-36,'JONY / INTENSIVE')
    for band in range(6): c.drawImage(str(ROOT/'public/student-design/pattern.png'),36+band*(w-72)/6,h-57,(w-72)/6,(w-72)/6*690/8147,mask='auto')
    c.setStrokeColor(LINE);c.line(36,32,w-36,32);c.setFont('Jony',8);c.drawString(36,19,'Noldan B2 sari · O‘rganish → mashq → tekshirish');c.drawRightString(w-36,19,str(doc.page));c.restoreState()
def save(name,story,size=A4):
    doc=SimpleDocTemplate(str(OUT/name),pagesize=size,rightMargin=36,leftMargin=36,topMargin=65,bottomMargin=47,title='Jony Intensive · '+name,author='Jony Academy')
    doc.build(story,onFirstPage=frame,onLaterPages=frame);print(name)
def cover(title,subtitle,notes):
    return [Spacer(1,35),p('NOLDAN B2 TOMON','sub'),p(title,'title'),p(subtitle,'h'),Spacer(1,15),p(notes),Spacer(1,20),p(f"{len(D['words']):,} ta so‘z · 192 dars · 8 oy".replace(',', ' '),'sub'),p('Grammar, lug‘at va to‘rt ko‘nikma materiallari darslarga bog‘langan. Bu Jony ichki o‘quv kursi; mashq natijalari milliy sertifikat bali o‘rnini bosmaydi.'),PageBreak()]
def table(rows,widths):
    t=Table([[p(cell,'cell') for cell in row] for row in rows],colWidths=widths,repeatRows=1,hAlign='LEFT')
    t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#E5EDFF')),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,PALE]),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),7),('RIGHTPADDING',(0,0),(-1,-1),7),('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7),('LINEBELOW',(0,0),(-1,-1),.35,LINE)]));return t

if 'teacher' in SECTIONS:
    # Regenerate from the exact pure UI module, never from a stale copied timeline.
    subprocess.run(['node', str(ROOT/'scripts/export-intensive-teaching.cjs')], cwd=ROOT, check=True)
    kits=json.loads((ROOT/'_inbox/intensive-teacher-kits.json').read_text(encoding='utf-8'))
    assert len(kits)==192
    def teacher_book(selected, name, subtitle):
        story=cover('Ustoz to‘plami',subtitle,'Saytdagi dars rejasiga mos: darsga mos vaqt, aniq mashq raqamlari, javob, uy vazifasi va keyingi ustozga topshirish. 16 o‘quvchilik guruh uchun; Sayt orqali guruh hajmini moslang. Kalitlar faqat ustoz uchun.')
        for k in selected:
            assert k['totalMinutes']==120
            story += [p(f"{k['lesson']}-dars / {k['week']}-hafta / {k['month']}-oy",'title'),p(k['profileLabel'],'sub'),p(k['objective']),p(k['boundary'])]
            m=k['materials']
            for label,value in [('Doska', '\n'.join(m['board'])),('Tushuntirish',m['explain']),('Xato',m['commonMistake']),('Yordam',m['differentiation'])]:
                story += [p(label,'sub'),p(value,'small')]
            for stage in k['stages']:
                story += [p(f"{stage['start']}–{stage['end']} · {stage['title']}",'sub'),p(stage['instruction'],'small'),p('ID: '+', '.join(stage['exerciseIds']),'small')]
            if k['exam']: story += [p(k['exam']['notice'],'small')]
            story += [p('Asosiy mashqlar — qisqa havolalar','sub'),p(', '.join(k['mandatoryExerciseIds']),'small'),p('Savollar va javoblar — ustoz uchun','h')]
            required=set(k['mandatoryExerciseIds'])|{x for h in k['homework'] for x in h['exerciseIds']}
            for q in k['questions']:
                if q['id'] in required:
                    story += [p(q['id']+' · '+q['prompt'],'small'),p('Javob: '+' / '.join(q['answers'])+'. '+q['explanation'],'small')]
            story += [p('Bugungi lug‘at','h')]
            for w in m['vocabulary']:
                story += [p(f"{w['id']} · {w['word']} {w['ipa']} — {w['meaning']}",'small'),p(w['example']+' · '+w['translation'],'small')]
            audio_url='https://jonyos.uz'+m['audioUrl']
            story += [Paragraph(f'<link href="{audio_url}" color="#2162E8">Dars audiosi: {audio_url}</link>',styles['small'])]
            skills=m['skills']
            if skills:
                for mode in ['reading','listening']:
                    story += [p(mode.title()+' · '+skills[mode]['title'],'sub'),p(skills[mode]['text'],'small')]
                for mode in ['speaking','writing']:
                    story += [p(mode.title(),'sub'),p(skills[mode]['prompt'],'small'),p('Mezon: '+' · '.join(skills[mode]['success']),'small')]
                story += [p('Writing namuna — urinishdan keyin','sub'),p(skills['writing']['model'],'small')]
            if m.get('previousSkills'):
                prev=m['previousSkills']
                story += [p('Uy vazifasi uchun oldingi dars materiallari','h')]
                for mode in ['reading','listening']:
                    story += [p(prev[mode]['title'],'sub'),p(prev[mode]['text'],'small')]
                story += [p('Oldingi writing namuna', 'sub'),p(prev['writing']['model'],'small'),p(' · '.join(prev['writing']['success']),'small'),p(' · '.join(prev['speaking']['success']),'small')]
            story += [p('Qo‘shimcha bank','sub'),p(k['extensionInstruction'],'small')]
            for q in k['questions']:
                if q['id'] in k['extensionExerciseIds'] and q['id'] not in required:
                    story += [p(q['id']+' · '+q['prompt'],'small'),p('Javob: '+' / '.join(q['answers'])+'. '+q['explanation'],'small')]
            story += [p('Chiqish bileti — ustoz kaliti','sub')]+[p(x,'small') for x in k['exitTicket']]
            if k.get('unseenHomework'):
                weekly=k['unseenHomework']
                story += [p(f"{weekly['week']}-hafta yangi mustaqil matni",'h'),p(weekly['title'],'sub'),p(weekly['instructions'],'small'),p(weekly['text'],'small')]
                for task in weekly['tasks']:
                    story += [p(task['id']+' · '+task['prompt'],'small')]+[p(option,'small') for option in task['options']]
                    story += [p('Ustoz kaliti: '+task['teacher']['answer'],'small'),p('Dalil: '+' / '.join(task['teacher']['evidence']),'small')]
            story += [p(f"Uy vazifasi · {k['homeworkMinutes']} daqiqa asosiy",'h')]
            for h in k['homework']: story += [p(f"{h['minutes']} daqiqa · {h['task']}",'small')]
            story += [p('Keyingi ustozga topshirish','h'),p(k['handoff']['nextObjective'],'small'),p(k['handoff']['instruction'],'small')]
            story += [p(x+': ____________________','small') for x in k['handoff']['fields']]
            story.append(PageBreak())
        save(name,story[:-1])
    teacher_book(kits,'jony-intensive-teacher-guide.pdf','8 oy · 32 hafta · 192 dars')
    for month in range(1,9):
        teacher_book([k for k in kits if k['month']==month],f'jony-intensive-month-{month}-teacher.pdf',f'{month}-oy · 24 dars')


if 'vocabulary' in SECTIONS:
    # Branded vocabulary reference, ten words per page.
    def vocabulary_book(pool, name, title):
        story=cover('Vocabulary Map',title,'So‘z / transkripsiya / tarjima / esda qoladigan misol / gap tarjimasi. Har 10 so‘zni o‘rganib mashq qiling; har 20 so‘zdan keyin aralash qaytaring.')
        blocks=[]
        for word in pool:
            if not blocks or len(blocks[-1])==10 or blocks[-1][-1]['topic']!=word['topic']: blocks.append([])
            blocks[-1].append(word)
        for block in blocks:
            story += [p(block[0]['topic'],'h')]
            story.append(table([['SO‘Z / IPA','TARJIMA','MISOL GAP','GAP TARJIMASI']]+[[f"{w['id']:04d} {w['word']}\n{w['ipa']}",w['meaning'],w['example'],w['translation']] for w in block],[155,140,240,234]))
            story += [Spacer(1,12),p('O‘zlashtirish: □ Taniyman    □ To‘g‘ri aytaman    □ Gapda ishlataman','small'),PageBreak()]
        save(name,story[:-1],landscape(A4))
    vocabulary_book(D['words'],'jony-vocabulary-001-4000.pdf','001–4000 · Britaniya IPA')
    for month in range(1,9):
        vocabulary_book(D['words'][(month-1)*500:month*500],f'jony-intensive-month-{month}-vocabulary.pdf',f'{month}-oy · {(month-1)*500+1:04d}–{month*500:04d}')

    # Student vocabulary worksheet with keys in a separate section.
    story=cover('Vocabulary mashqlari','Har 10 so‘z · har 20 so‘z aralash','Avval javoblarni yopib ishlang. Xato so‘zni ertasi kuni, 3-kuni va 7-kuni yana tekshiring. Javoblar kitob oxirida; o‘quvchiga tarqatishda ularni alohida chop eting.')
    keys=[]
    for size in [10,20]:
        for start in range(0,len(D['words']),size):
            pool=D['words'][start:start+size];random.Random(start+size).shuffle(pool)
            title=f'{start+1}–{start+size} · '+('Aralash takrorlash' if size==20 else '10 so‘z mashqi')
            story += [p(title,'h'),p('Ism: ____________________   Sana: __________   Natija: ____ / '+str(size),'small')];answers=[]
            for i,w in enumerate(pool):
                pattern=r'(?<![a-z])'+re.escape(w['word'])+r'(?:s|es)?(?![a-z])'
                match=re.search(pattern,w['example'],re.I)
                if i%2 and match:
                    question=re.sub(pattern,'________',w['example'],count=1,flags=re.I);answer=match[0]
                    hint=w['translation']
                else:question=f"Inglizcha bosh so‘z: {w['meaning']}  ____________________";answer=w['word'];hint=''
                story.append(KeepTogether([p(f'{i+1}. {question}','p' if size==10 else 'small'),p(hint,'small') if hint else Spacer(1,1),Spacer(1,8 if size==10 else 2)]));answers.append(f'{i+1}. {answer}')
            story += [p('Mustaqil: shu so‘zlardan 3 tasi bilan yangi kulgili gaplar yozing. Ustoz shakl va ma’noni tekshiradi.','small'),PageBreak()];keys.append((title,' · '.join(answers)))
    story += [p('Javoblar · ustoz uchun','title')]
    for title,answers in keys:story.append(KeepTogether([p(title,'sub'),p(answers,'small'),Spacer(1,8)]))
    save('jony-intensive-vocabulary-workbook.pdf',story)


if 'grammar' in SECTIONS:
    # Every map topic gets analysis, exact-model reconstruction and independent production.
    story=cover('Grammar mashqlari',f"{len(D['topics'])} mavzu · 27 bo‘lim · {sum(len(v) for v in D['topicExercises'].values())+len(D['checks'])} izohli tekshiruv savoli",'Har mavzuda: tuzilmani tahlil qilish, namunani tiklash, oltita yangi tekshiruv savoli va ikki mustaqil misol. Javoblar kitob oxirida; erkin gaplarni ustoz tekshiradi.')
    for mi,module in enumerate(D['grammar']):
        story += [p(f'{mi+1}. {module["title"]}','title'),p(module['goal'])]
        story += [p('Ustozga: '+NOTES[mi][0],'small'),p('Tushunishni tekshiring: '+NOTES[mi][1],'small'),p('Xatolar: '+NOTES[mi][2],'small'),Spacer(1,10)]
        for ti,(title,example) in enumerate(module['items']):
            chunks=example.split();random.Random(mi*100+ti).shuffle(chunks)
            story.append(KeepTogether([p(f'{mi+1}.{ti+1} · {title}','sub'),p('Namuna: '+example,'small'),p('1. Shu mavzuga tegishli shaklni belgilang. Ma’nosini tushuntiring.','small'),p('2. Namunani yoping. Qayta tartiblang: '+' / '.join(chunks),'small'),p('________________________________________________________','small'),p('3. Shu shaklda ikki yangi gap yoki birikma tuzing; bittasida yangi lug‘atni ishlating.','small'),p('________________________________________________________\n________________________________________________________','small'),Spacer(1,9)]))
        story += [p('Mavzu bo‘yicha yangi savollar','h')]
        for ti,_ in enumerate(module['items']):
            topic_id=f'{mi+1}.{ti+1}'
            for qi,q in enumerate(D['topicExercises'][topic_id],1):
                story.append(KeepTogether([p(f'{topic_id}/{qi}. {q["prompt"]}','small'),p('Javob: __________________________________________','small')]))
        story.append(PageBreak())
    story += [p('Aralash grammatika nazorati','title'),p('Bo‘limlar o‘tilgandan keyin ishlang. Javoblar keyingi bo‘limda.')]
    for i,q in enumerate(D['checks']):story.append(KeepTogether([p(f'{i+1}. {q["prompt"]}'),p('Javob: ____________________','small')]))
    story += [PageBreak(),p('Nazorat javoblari va izohlar','title')]
    for i,q in enumerate(D['checks']):story.append(KeepTogether([p(f'{i+1}. '+ ' / '.join(q['answers']),'sub'),p(q['explanation'],'small')]))
    story += [PageBreak(),p('Mavzu savollari: javob va sabab','title')]
    for topic_id,questions in D['topicExercises'].items():
        for qi,q in enumerate(questions,1):
            story.append(KeepTogether([p(f'{topic_id}/{qi}. '+ ' / '.join(q['answers']),'sub'),p(q['explanation'],'small')]))
    save('jony-intensive-grammar-workbook.pdf',story)
