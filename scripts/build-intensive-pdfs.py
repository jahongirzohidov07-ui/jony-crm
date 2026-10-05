"""Build printable reviewed materials from the same course export as the UI.
Run node scripts/test-intensive.cjs --export first. Requires reportlab.
"""
from pathlib import Path
from xml.sax.saxutils import escape
import json, re, random
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'public/intensive'
D=json.loads((OUT/'course-export.json').read_text(encoding='utf-8'))
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
    c.setStrokeColor(LINE);c.line(36,32,w-36,32);c.setFont('Jony',8);c.drawString(36,19,'Noldan B2 sari · O‘rganish → mashq → tekshirish');c.drawRightString(w-36,19,str(doc.page));c.restoreState()
def save(name,story,size=A4):
    doc=SimpleDocTemplate(str(OUT/name),pagesize=size,rightMargin=36,leftMargin=36,topMargin=65,bottomMargin=47,title='Jony Intensive · '+name,author='Jony Academy')
    doc.build(story,onFirstPage=frame,onLaterPages=frame);print(name)
def cover(title,subtitle,notes):
    return [Spacer(1,35),p('NOLDAN B2 TOMON','sub'),p(title,'title'),p(subtitle,'h'),Spacer(1,15),p(notes),Spacer(1,20),p('Ishchi nashr · 500 ta tayyor so‘z / 4 000 ta reja','sub'),p('Lug‘atning 501–4000 qismi va to‘liq darajaviy reading/listening hamda sinov to‘plamlari hali tayyor emas. Rejalashtirilgan dars bilan to‘liq tayyor dars farqlanadi.'),PageBreak()]
def table(rows,widths):
    t=Table([[p(cell,'cell') for cell in row] for row in rows],colWidths=widths,repeatRows=1,hAlign='LEFT')
    t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#E5EDFF')),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,PALE]),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),7),('RIGHTPADDING',(0,0),(-1,-1),7),('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7),('LINEBELOW',(0,0),(-1,-1),.35,LINE)]));return t

# Teacher playbook: daily instructions and exact assigned topic IDs, not an empty calendar.
story=cover('Ustoz qo‘llanmasi','8 oy · 32 hafta · 192 dars','Har yangi ustoz bir xil tartibda ishlashi uchun: dars oldi tayyorgarlik, 120 daqiqalik ssenariy, mavzu va so‘z oralig‘i, 120 daqiqalik uy vazifasi, tekshiruv mezonlari.')
story += [p('Kursdan foydalanish','title'),p('1. Oy → hafta → darsni oching. Bugungi grammar kartalari va so‘zlarni ko‘rib chiqing.\n2. Har shakl: namuna → birga mashq → mustaqil ishlatish.\n3. Har 10 so‘zdan keyin mashq; har 20 so‘zdan keyin aralash qaytarish.\n4. Javoblarni oldindan ko‘rsatmang. Tekshirgach xatolarni qayta ishlang.\n5. Har haftaning 6-kuni yangi material emas, aralash mashq va tekshiruv.\n6. 32 hafta — o‘quv bloki. Bayram va qayta o‘tishlar kalendardagi zaxira kunlariga joylanadi.'),p('Birinchi dars: orientatsiya','h'),p('0–15: kurs maqsadi. 15–30: xarita, daftar va uy vazifasi tartibi. 30–45: noun va adjective. 45–60: birinchi 10 so‘z. 60–65: tanaffus. 65–80: keyingi so‘zlar. 80–95: mashqni birga bajarish. 95–110: tinglash va gapirish. 110–120: uy ishini namoyish qilish.'),p('Natijani qanday tekshiramiz?','h'),p('Chiqish bileti: 3 so‘z + 2 grammar savoli. 4/5 dan past bo‘lsa, keyingi dars boshida aynan xato mavzu qaytariladi. Erkin gaplarda shakl, ma’no va yangi lug‘atni mustaqil ishlatish tekshiriladi. Onlayn mashq ballari rasmiy baho sifatida saqlanmaydi.'),p('Material tayyorligi','h'),p('192 darsning taqsimoti bor. 1–500 so‘z, har mavzu uchun namuna-tahlil va mustaqil mashq, 54 ta izohli grammar savoli tayyor. Bu to‘liq 8 oylik darslik yoki sertifikat mock banki tayyor degani emas.'),PageBreak()]
for key,title in [('timeline','Oddiy dars · 120 daqiqa'),('reviewTimeline','Takrorlash darsi · 120 daqiqa'),('homework','Uy vazifasi · 120 daqiqa')]:
    story.append(p(title,'title'));minute=0
    for duration,label,instruction in D[key]:
        story.append(KeepTogether([p(f'{minute}–{minute+duration} daqiqa · {label}','sub'),p(instruction)]));minute+=duration
    assert minute==120;story.append(PageBreak())
for week in range(1,33):
    lessons=D['lessons'][(week-1)*6:week*6]
    story += [p(f'{(week-1)//4+1}-oy / {week}-hafta','title'),p(' · '.join(D['grammar'][i]['title'] for i in lessons[0]['moduleIds']),'h'),p(f'Lug‘at: {(week-1)*125+1}–{week*125}. Har yangi darsda 25 so‘z: avval 10 + 10, so‘ng 5 qo‘shimcha. Har 6-kun — takrorlash.','small')]
    for lesson in lessons:
        ids=', '.join(t['id'] for t in lesson['topics'])
        titles='; '.join(t['title'] for t in lesson['topics'])
        if lesson['review']:titles='Hafta grammatikasi, 20 aralash so‘z, tinglash va erkin gaplar; xatolarni tuzatish.'
        status='Lug‘at tayyor' if lesson['wordsReady'] else f"Lug‘at to‘liq emas: {len(lesson['words'])}/{lesson['end']-lesson['start']+1}"
        story.append(KeepTogether([p(f"{lesson['no']}-dars · {lesson['day']}-kun",'sub'),p(titles,'small'),p(f"Grammar kartalari: {ids}\nSo‘zlar {lesson['start']}–{lesson['end']} · {status}",'small')]))
    story += [p('Uyga vazifa: yuqoridagi 120 daqiqalik uy ishi tartibi, faqat bugun o‘tilgan mavzu va so‘zlar. Keyingi darsda 5 so‘z va 2 yangi gap bilan tekshiring.','small'),PageBreak()]
save('jony-intensive-teacher-guide.pdf',story[:-1])

# Branded vocabulary reference, ten words per page.
story=cover('Vocabulary Map','001–500 · 50 mavzu · Britaniya IPA','So‘z / transkripsiya / tarjima / esda qoladigan misol / gap tarjimasi. Misollar xayoliy va kulgili; yangi grammatik shakllarni ustoz izohlaydi.')
for start in range(0,len(D['words']),10):
    pool=D['words'][start:start+10];story+=[p(pool[0]['topic'],'h')]
    story.append(table([['SO‘Z / IPA','TARJIMA','MISOL GAP','GAP TARJIMASI']]+[[f"{w['id']:03d} {w['word']}\n{w['ipa']}",w['meaning'],w['example'],w['translation']] for w in pool],[155,140,240,234]))
    story += [Spacer(1,12),p('O‘zlashtirish: □ Taniyman    □ To‘g‘ri aytaman    □ Gapda ishlataman','small'),PageBreak()]
save('jony-vocabulary-001-500.pdf',story[:-1],landscape(A4))

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

# Every map topic gets analysis, exact-model reconstruction and independent production.
story=cover('Grammar mashqlari',f"{len(D['topics'])} mavzu · 27 bo‘lim · 54 izohli nazorat savoli",'Har mavzuda: tuzilmani tahlil qilish, namunani qayta tiklash, ikki mustaqil misol. Namuna tiklash — model bilan ishlash; erkin gaplarni ustoz tekshiradi.')
for mi,module in enumerate(D['grammar']):
    story += [p(f'{mi+1}. {module["title"]}','title'),p(module['goal'])]
    story += [p('Ustozga: '+NOTES[mi][0],'small'),p('Tushunishni tekshiring: '+NOTES[mi][1],'small'),p('Xatolar: '+NOTES[mi][2],'small'),Spacer(1,10)]
    for ti,(title,example) in enumerate(module['items']):
        chunks=example.split();random.Random(mi*100+ti).shuffle(chunks)
        story.append(KeepTogether([p(f'{mi+1}.{ti+1} · {title}','sub'),p('Namuna: '+example,'small'),p('1. Shu mavzuga tegishli shaklni belgilang. Ma’nosini tushuntiring.','small'),p('2. Namunani yoping. Qayta tartiblang: '+' / '.join(chunks),'small'),p('________________________________________________________','small'),p('3. Shu shaklda ikki yangi gap yoki birikma tuzing; bittasida yangi lug‘atni ishlating.','small'),p('________________________________________________________\n________________________________________________________','small'),Spacer(1,9)]))
    story.append(PageBreak())
story += [p('Aralash grammatika nazorati','title'),p('Bo‘limlar o‘tilgandan keyin ishlang. Javoblar keyingi bo‘limda.')]
for i,q in enumerate(D['checks']):story.append(KeepTogether([p(f'{i+1}. {q["prompt"]}'),p('Javob: ____________________','small')]))
story += [PageBreak(),p('Nazorat javoblari va izohlar','title')]
for i,q in enumerate(D['checks']):story.append(KeepTogether([p(f'{i+1}. '+ ' / '.join(q['answers']),'sub'),p(q['explanation'],'small')]))
save('jony-intensive-grammar-workbook.pdf',story)
