"""Build Jony German course books from the same JSON used by the app."""
import json
import argparse
import os
import subprocess
from pathlib import Path
from xml.sax.saxutils import escape
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, KeepTogether, Table, TableStyle

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'src/data/german'
OUT = ROOT / 'public/german'
OUT.mkdir(parents=True, exist_ok=True)
parser = argparse.ArgumentParser()
parser.add_argument('--skip-vocabulary', action='store_true', help='Retain unchanged vocabulary PDFs')
parser.add_argument('--site-url', default=os.environ.get('COURSE_PUBLIC_URL', ''), help='Public app origin for absolute MP3 links; otherwise links are relative to this PDF in /german/')
args = parser.parse_args()
teaching = json.loads(subprocess.check_output(['node', str(ROOT/'scripts/export-german-teaching.cjs')], cwd=ROOT, encoding='utf-8'))
kits = {k['no']: k for k in teaching['lessons']}
extra = {t['topicId']: [] for t in teaching['exercises']}
for exercise in teaching['exercises']: extra[exercise['topicId']].append(exercise)

read = lambda name: json.loads((DATA / name).read_text(encoding='utf-8'))
words = sum([read(f'vocabulary-{n}.json') for n in range(1,4)], [])
grammar, lessons, skills = read('grammar.json'), read('lessons.json'), read('skills.json')
for name, file in [('Jony','arial.ttf'),('JonyBold','arialbd.ttf')]:
    pdfmetrics.registerFont(TTFont(name, 'C:/Windows/Fonts/' + file))
pdfmetrics.registerFontFamily('Jony', normal='Jony', bold='JonyBold')
BLUE, NAVY = colors.HexColor('#2162e8'), colors.HexColor('#10213b')
STYLES = {k: ParagraphStyle(k, fontName='JonyBold' if bold else 'Jony', fontSize=size, leading=size*1.4, textColor=color, spaceAfter=space) for k,size,bold,color,space in [('title',25,True,NAVY,18),('h',15,True,NAVY,10),('sub',11,True,BLUE,7),('p',10,False,NAVY,6),('small',8,False,NAVY,5)]}
STYLES['cell'] = ParagraphStyle('cell',fontName='Jony',fontSize=8.5,leading=10,textColor=NAVY)
def p(text, style='p'):
    return Paragraph(escape(str(text)).replace('\n','<br/>'), STYLES[style])
def frame(c, doc):
    w,h = doc.pagesize
    c.saveState()
    c.drawImage(str(ROOT/'src/assets/brand-icon.png'),36,h-45,23,23,mask='auto')
    c.setFont('JonyBold',11);c.setFillColor(BLUE);c.drawString(70,h-37,'JONY DEUTSCH / B1')
    pattern = ROOT/'public/student-design/pattern.png'
    if pattern.exists():
        for band in range(6): c.drawImage(str(pattern),36+band*(w-72)/6,h-58,(w-72)/6,(w-72)/6*690/8147,mask='auto')
    c.setStrokeColor(colors.HexColor('#dfe6f0'));c.line(36,34,w-36,34)
    c.setFont('Jony',8);c.setFillColor(NAVY);c.drawString(36,21,'6 oy · 24 hafta · Asosiy dars + support + mustaqil ish');c.drawRightString(w-36,21,str(doc.page));c.restoreState()
def save(name, story, size=A4):
    SimpleDocTemplate(str(OUT/(name+'.pdf')),pagesize=size,leftMargin=36,rightMargin=36,topMargin=72,bottomMargin=48,title='Jony Deutsch · '+name,author='Jony Academy').build(story,onFirstPage=frame,onLaterPages=frame)
    print(name)
def cover(title, subtitle, note):
    return [Spacer(1,32),p(title,'title'),p(subtitle,'h'),p(note),p('Jony mualliflik o‘quv materiali. Goethe-Institutning rasmiy testi emas.','small'),PageBreak()]

def vocabulary(pool, name, title):
    story=cover('Vocabulary Map',title,'So‘z va iboralarni artikl, talaffuz va misol bilan o‘rganing. Har 10/20 so‘zdan keyin saytdagi mashqni bajaring. 1, 3 va 7 kundan keyin qaytaring.')
    for i in range(0,len(pool),10):
        block=pool[i:i+10]
        if i: story.append(PageBreak())
        story.append(p(f"{block[0]['week']}-hafta · #{block[0]['id']}–{block[-1]['id']}",'h'))
        rows=[['SO‘Z / IPA / SHAKLLAR','MA’NO','NEMISCHA MISOL','GAP TARJIMASI']]
        rows += [[f"{w['id']}. {w['word']}\n{w['ipa']}\n{w['forms']}",w['meaning'],w['example'],w['translation']] for w in block]
        table=Table([[p(cell,'cell') for cell in row] for row in rows],colWidths=[190,110,235,landscape(A4)[0]-72-535],repeatRows=1,hAlign='LEFT')
        table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#dbeafe')),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#f3f6fc')]),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),7),('RIGHTPADDING',(0,0),(-1,-1),7),('TOPPADDING',(0,0),(-1,-1),4),('BOTTOMPADDING',(0,0),(-1,-1),4),('LINEBELOW',(0,0),(-1,0),1,BLUE),('LINEBELOW',(0,1),(-1,-1),0.3,colors.HexColor('#dfe6f0'))]))
        story += [table,Spacer(1,10),p('O‘zimni tekshirish: □ Ma’nosini bilaman   □ Talaffuz qilaman   □ Gapda ishlataman','small')]
    save(name,story,landscape(A4))
if not args.skip_vocabulary:
    vocabulary(words,'jony-deutsch-vocabulary','0 → B1 · 2 400 so‘z va ibora')
    for month in range(1,7): vocabulary(words[(month-1)*400:month*400],f'jony-deutsch-month-{month}-vocabulary',f'{month}-oy · 400 so‘z')

def timeline(rows):
    result=[]
    end=0
    for minutes,title,text in rows:
        start=end; end+=minutes
        result += [p(f'{start}–{end} daqiqa · {title}','sub'),p(text)]
    return result

def audio_link(no):
    path=kits[no]['audioPath']
    url=args.site_url.rstrip('/')+path if args.site_url else 'audio/'+path.rsplit('/',1)[-1]
    return Paragraph('Sun’iy ovozli dars yozuvi · <link href="'+escape(url, {'"':'&quot;'})+'" color="#2162e8">MP3: '+escape(path)+'</link>',STYLES['small'])

def exercise_flow(e, answers=False):
    result=[p(e['id']+' · '+e['kind'],'sub'),p(e['prompt'])]
    if answers:
        result += [p('Namuna: '+e['model'],'sub'),p(e['guidance'])]+[p('• '+c,'small') for c in e['criteria']]
    else:
        result += [p('Javob / yangi vaziyat: __________________________________________'),Spacer(1,12)]
    return result

def checkpoint_flow(c, answers=False):
    result=[p(str(c['no']//12)+'-oy · ichki nazorat'+(' / USTOZ KALITI' if answers else ''),'title'),p(c['administration'])]
    for kind,label in [('reading','Lesen'),('listening','Hören')]:
        result += [p(label,'h')]
        if kind=='reading' or answers: result += [p(c[kind])]
        else: result += [p('Ustoz skriptni ikki marta o‘qiydi. Bu nazorat skripti dars MP3sidan alohida.')]
        for i,(q,a) in enumerate(c[kind+'Questions'],1):
            result += [p(f'{i}. {q}'+(' — '+a if answers else '')),p('Javob: ____________________','small') if not answers else Spacer(1,4)]
    result += [p('Grammatika · avval o‘tilgan mavzular','h')]
    for e in c['grammar']: result += exercise_flow(e, answers)
    result += [p('Avvalgi faol lug‘at','h')]
    for v in c['vocabulary']: result += [p(v['prompt']+(' — #'+str(v['id'])+' '+v['answer'] if answers else '')),Spacer(1,8)]
    for kind,label in [('speaking','Sprechen'),('writing','Schreiben')]:
        result += [p(label,'h'),p(c[kind])]
        if answers: result += [p('Namuna: '+c[kind+'Model'])]
        result += [p('0 / 1 / 2: '+criterion,'small') for criterion in c['rubric'][kind]]
    result += [p(c['rubric']['objective']),p(c['rubric']['anchors']),p(c['rubric']['decision'])]
    if answers: result += [p(c['retest'])]
    result += [p('O‘quvchi ___ · Lesen __/3 · Hören __/3 · grammatika __/4 · lug‘at __/4 · nutq __/6 · yozuv __/6 · keyingi qadam ___')]
    return result

story=cover('Grammar Map','A1 → A2 → B1','Har mavzuni qoida, namuna va mustaqil mashq bilan o‘rganing. Javoblar alohida kitobda. Katta harf, umlaut, artikl va fe’l o‘rnini tekshiring.')
keys=cover('Grammar · javoblar','Ustoz uchun','O‘quvchi mustaqil bajargach oching. To‘g‘ri javob bilan birga sababni tushuntiring.')
for topic in grammar:
    story += [p(f"{topic['id']} · {topic['title']}",'h'),p(topic['level'],'sub'),p(topic['rule']),p(topic['example'],'sub'),p(topic['translation'])]
    keys += [p(f"{topic['id']} · {topic['title']}",'h')]
    for i,q in enumerate(topic['questions'],1):
        story += [p(f"{i}. {q['prompt']}"),p('Javob: ____________________________________________________','small'),Spacer(1,8)]
        keys += [p(f"{i}. {' / '.join(q['answers'])}",'sub'),p(q['explanation'])]
    for e in extra[topic['id']]:
        story += exercise_flow(e)
        keys += exercise_flow(e, True)
    story.append(PageBreak());keys.append(Spacer(1,15))
save('jony-deutsch-grammar',story[:-1]);save('jony-deutsch-answer-key',keys)

story=cover('Kurs xaritasi va darslar','Ustoz kiti · yangilangan darslar','24 hafta. Har hafta 3 × 120 daqiqa asosiy dars, 3 × 60 daqiqa support. Har kuni 75 daqiqa mustaqil ish, haftada 6 kun; asosiy va support kunlari vazifalari farqlanadi. 10–15 faol so‘z; qolgan lug‘at retseptiv. Sertifikat kafolati emas.')
story += [p('Darsni boshqarish','h'),p('Har darsning aniq jadvali quyida. 12/24/36/48/60-darslarda yangi ichki nazorat, 49-darsdan qisqa format mashqlari. 61/64/67-darslarda to‘liq rasmiy Lesen/Hören/Schreiben; yangi grammatika o‘sha kunning supportida. 70–72-darslar rasmiy namunalar bilan saqlangan; yangi grammatika kiritilmaydi.'),p('Grammatika kitobida har mavzuga 3 qisqa tekshiruv va 3 yangi production/correction/transfer topshirig‘i bor. Bir kunda hammasini bajartirmang: asosiy dars, support va ehtiyojga qarab tanlang.'),p(teaching['examSource']['note']),p('Manba: '+teaching['examSource']['url']+' · '+teaching['examSource']['checked'],'small'),p('MP3 havolalari saytdagi PDF joylashuviga nisbatan. Yuklab olingan nusxa uchun saytning /german/audio/ manzilidan foydalaning.' if not args.site_url else 'MP3 havolalari: '+args.site_url,'small'),PageBreak()]
for lesson in lessons:
    kit=kits[lesson['no']]; v=kit['vocabulary']
    story += [p(f"{lesson['no']}-dars · {lesson['title']}",'title'),p(lesson['objective']),p(lesson['teacherTip']),audio_link(lesson['no']),p('Faol lug‘at · asosiy darsda tanishtirish, supportda qaytarish','h'),p('; '.join('#'+str(w['id'])+' '+w['word'] for w in v['active'])),p('Retseptiv / supportda ma’noni tanish · majburiy faol yodlash emas','h'),p('; '.join('#'+str(w['id'])+' '+w['word'] for w in v['receptive'])),p('Oldingi faol IDlar: '+', '.join('#'+str(i) for i in v['reviewIds'])),p('Asosiy dars · 120 daqiqa','h')]
    if kit['officialPractice']:
        official=kit['officialPractice']
        story += [p('Rasmiy modul: '+official['module'],'h'),p(official['material']),p(official['url'],'small'),p(official['validity']),p(official['remediation'])]
    story += timeline(kit['timeline'])
    story += [p(kit['speaking']),p('Support · 60 daqiqa','h')]+timeline(kit['support'])
    story += [p('Ustozlar o‘rtasidagi qayd','h'),p(kit['handoff']),p('Uy vazifasi · vaqt chegarasi','h'),p(kit['workload'])]+timeline(kit['homework'])
    story += [p('Support kuni · 75 daqiqa','h')]+timeline(kit['supportDayHomework'])
    story += [p('Grammatika kitobi: '+', '.join(kit['topicIds'])+'. Yangi mavzular bo‘lsa darsda bir production, supportda correction/transfer. Yakuniy haftada faqat xatoga mos takror.','small'),PageBreak()]
    if kit['checkpoint']:
        story += checkpoint_flow(kit['checkpoint'], True)+[PageBreak()]
save('jony-deutsch-course-map',story[:-1])

for month in range(1,7):
    story=cover(f'{month}-oy · ko‘nikma daftari','Lesen · Hören · Sprechen · Schreiben','Mualliflik mashqlari. Saqlangan sun’iy ovozli MP3 yozuvini ikki marta tinglang; havola har darsda. Transkript faqat tekshiruvdan keyin ochiladi. MP3 mavjud bo‘lmasa ustoz o‘qiydi. Ichki oylik nazoratning alohida skriptini ustoz o‘qiydi.')
    answers=[]
    for s in skills[(month-1)*12:month*12]:
        story += [p(f"{s['no']}-dars",'title'),p('Lesen · '+s['reading']['title'],'h'),p(s['reading']['text'])]
        for section in ['reading','listening']:
            if section=='listening': story += [p('Hören · '+s[section]['title'].split(' — ')[0],'h'),audio_link(s['no']),p('Transkript ustoz bo‘limida. Avval tinglang va savollarga javob bering.')]
            for i,q in enumerate(s[section]['questions'],1): story += [p(f"{i}. {q['prompt']}"),p('Javob: ____________________________________________________','small')]
        for kind,label in [('speaking','Sprechen'),('writing','Schreiben')]:
            story += [p(label,'h'),p(s[kind]['task'])]+[p('• '+c,'small') for c in s[kind]['criteria']]
        story.append(PageBreak())
        answers += [p(f"{s['no']}-dars · kalit va namunalar",'title'),p('Hören · transkript','h'),p(s['listening']['text'])]
        for kind in ['reading','listening']:
            answers += [p(kind,'h')]+[p(f"{i+1}. {' / '.join(q['answers'])} — {q['explanation']}") for i,q in enumerate(s[kind]['questions'])]
        for kind in ['speaking','writing']: answers += [p(kind+' · namuna','h'),p(s[kind]['model'])]
        answers.append(PageBreak())
    checkpoint=kits[month*12]['checkpoint']
    if checkpoint:
        story += checkpoint_flow(checkpoint)+[PageBreak()]
        answers += checkpoint_flow(checkpoint, True)+[PageBreak()]
    story += [p('Ustoz bo‘limi','title'),p('Quyida transkriptlar, javoblar va namunalar. O‘quvchi nusxasini tarqatishda bu bo‘limni ajrating.'),PageBreak()] + answers
    save(f'jony-deutsch-month-{month}-skills',story[:-1])
