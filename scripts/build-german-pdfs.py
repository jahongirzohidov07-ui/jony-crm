"""Build Jony German course books from the same JSON used by the app."""
import json
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
vocabulary(words,'jony-deutsch-vocabulary','0 → B1 · 2 400 so‘z va ibora')
for month in range(1,7): vocabulary(words[(month-1)*400:month*400],f'jony-deutsch-month-{month}-vocabulary',f'{month}-oy · 400 so‘z')

story=cover('Grammar Map','A1 → A2 → B1','Har mavzuni qoida, namuna va mustaqil mashq bilan o‘rganing. Javoblar alohida kitobda. Katta harf, umlaut, artikl va fe’l o‘rnini tekshiring.')
keys=cover('Grammar · javoblar','Ustoz uchun','O‘quvchi mustaqil bajargach oching. To‘g‘ri javob bilan birga sababni tushuntiring.')
for topic in grammar:
    story += [p(f"{topic['id']} · {topic['title']}",'h'),p(topic['level'],'sub'),p(topic['rule']),p(topic['example'],'sub'),p(topic['translation'])]
    keys += [p(f"{topic['id']} · {topic['title']}",'h')]
    for i,q in enumerate(topic['questions'],1):
        story += [p(f"{i}. {q['prompt']}"),p('Javob: ____________________________________________________','small'),Spacer(1,8)]
        keys += [p(f"{i}. {' / '.join(q['answers'])}",'sub'),p(q['explanation'])]
    story.append(PageBreak());keys.append(Spacer(1,15))
save('jony-deutsch-grammar',story[:-1]);save('jony-deutsch-answer-key',keys)

story=cover('Kurs xaritasi va darslar','Goethe-Zertifikat B1 ga tayyorgarlik · 6 oy','24 hafta. Har hafta 3 × 120 daqiqa asosiy dars, 3 × 60 daqiqa support. Har kuni 75 daqiqa mustaqil ish (haftada 6 kun). Dastur natijasi oyma-oy tekshiriladi; sertifikat kafolati emas.')
story += [p('Ustozlar uchun yagona tartib','title'),p('Asosiy dars · 120 daqiqa','h'),p('0–10 eslash va uy vazifasi; 10–30 yangi grammatika; 30–45 boshqariladigan mashq; 45–60 birinchi 20 so‘z; 60–65 tanaffus; 65–80 qolgan lug‘at va Lesen; 80–95 Hören; 95–110 Sprechen va Schreiben; 110–120 chiqish bileti va uy vazifasi.'),p('1-dars · maxsus kirish tartibi','h'),p('0–10 xarita va tartib; 10–30 alifbo va talaffuz; 30–50 birinchi grammatika; 50–65 birinchi 10 so‘z; 65–70 tanaffus; 70–90 qolgan lug‘at; 90–105 o‘qish va tinglash; 105–115 o‘zi haqida gapirish va yozish; 115–120 uy vazifasini ko‘rsatish.'),p('Support · 60 daqiqa','h'),p('0–10 xatolar va uy vazifasi; 10–20 talaffuz va artikl; 20–35 20 so‘zli aralash mashq; 35–50 darsga mos amaliy juftlik; 50–55 tinglash ortidan takrorlash; 55–60 qayta tekshiruv.'),p('Mustaqil ish · 75 daqiqa','h'),p('20 daqiqa so‘zlar; 20 daqiqa grammatika; 15 daqiqa o‘qish yoki tinglash; 15 daqiqa yozish yoki gapirish; 5 daqiqa xato daftari. Har asosiy darsning so‘zlarini keyingi support kuni ham qaytaring.'),p('24-hafta · yakuniy sinov tartibi','h'),p('70-dars: 10 daqiqa ko‘rsatma, 65 Lesen, 20 lug‘at, 25 tahlil. 71-dars: 10 ko‘rsatma, 40 Hören rasmiy audio, 20 lug‘at, 30 juftlikda Sprechen, 20 tahlil. 72-dars: 10 ko‘rsatma, 60 Schreiben, 20 lug‘at, 15 tekshirish va 15 shaxsiy keyingi reja. Rasmiy namunalar havolasidan foydalaning. Gapirishni individual baholash uchun navbat belgilang.'),p('Nazorat','h'),p('Har oy grammatika/lug‘at mashqlarida ichki 80% mezon, erkin nutq va yozuvni ustoz tekshiradi. Past natijada xato mavzuga support ajrating va qayta tekshiring. B1 yakunida rasmiy Goethe namunasini to‘liq vaqt va ko‘rsatmalar bilan bajaring.'),p('Rasmiy format: https://www.goethe.de/ins/de/de/m/prf/prf/gzb1/inf.html','small'),p('Rasmiy sinovlar: https://www.goethe.de/ins/dk/de/spr/prf/ueb/pb1.html','small'),PageBreak()]
by_id={t['id']:t for t in grammar}
for l in lessons:
    pool=[w for w in words if w['week']==l['week']]; day=(l['no']-1)%3
    pool=pool[day*100//3:(day+1)*100//3]
    story += [p(f"{l['no']}-dars · {l['title']}",'title'),p(f"{l['month']}-oy / {l['week']}-hafta / {l['level']}",'sub'),p(l['objective']),p('Grammatika','h'),p('; '.join(f"{i}: {by_id[i]['title']}" for i in l['topicIds'])),p(f"Lug‘at: #{pool[0]['id']}–{pool[-1]['id']} ({len(pool)} ta)",'h'),p(l['teacherTip']),p('Support topshirig‘i','h'),p(l['supportTask']),p('Uyga vazifa','h')]
    story += [p(f'{i+1}. {h}') for i,h in enumerate(l['homework'])]
    story += [p(f"Lesen, Hören, Sprechen va Schreiben: {l['month']}-oy ko‘nikma daftarining {l['no']}-darsi.",'small'),PageBreak()]
save('jony-deutsch-course-map',story[:-1])

for month in range(1,7):
    story=cover(f'{month}-oy · ko‘nikma daftari','Lesen · Hören · Sprechen · Schreiben','Mualliflik mashqlari. Tinglashni ustoz transkriptdan ikki marta o‘qib beradi yoki saytdagi nemischa sintetik ovozdan foydalaning. O‘quvchi transkriptni savollardan keyin ochsin.')
    answers=[]
    for s in skills[(month-1)*12:month*12]:
        story += [p(f"{s['no']}-dars",'title'),p('Lesen · '+s['reading']['title'],'h'),p(s['reading']['text'])]
        for section in ['reading','listening']:
            if section=='listening': story += [p('Hören · '+s[section]['title'],'h'),p('Transkript ustoz bo‘limida. Avval tinglang va savollarga javob bering.')]
            for i,q in enumerate(s[section]['questions'],1): story += [p(f"{i}. {q['prompt']}"),p('Javob: ____________________________________________________','small')]
        for kind,label in [('speaking','Sprechen'),('writing','Schreiben')]:
            story += [p(label,'h'),p(s[kind]['task'])]+[p('• '+c,'small') for c in s[kind]['criteria']]
        story.append(PageBreak())
        answers += [p(f"{s['no']}-dars · kalit va namunalar",'title'),p('Hören · transkript','h'),p(s['listening']['text'])]
        for kind in ['reading','listening']:
            answers += [p(kind,'h')]+[p(f"{i+1}. {' / '.join(q['answers'])} — {q['explanation']}") for i,q in enumerate(s[kind]['questions'])]
        for kind in ['speaking','writing']: answers += [p(kind+' · namuna','h'),p(s[kind]['model'])]
        answers.append(PageBreak())
    story += [p('Ustoz bo‘limi','title'),p('Quyida transkriptlar, javoblar va namunalar. O‘quvchi nusxasini tarqatishda bu bo‘limni ajrating.'),PageBreak()] + answers
    save(f'jony-deutsch-month-{month}-skills',story[:-1])
