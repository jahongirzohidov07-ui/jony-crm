"""Printable course materials from the same 144 lessons rendered in the app."""
import json
from pathlib import Path
from xml.sax.saxutils import escape
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'public/russian'
OUT.mkdir(parents=True, exist_ok=True)
lessons = sum([json.loads((ROOT / f'src/data/russian/part-{i}.json').read_text(encoding='utf-8')) for i in range(1,5)], [])
assert [x['no'] for x in lessons] == list(range(1,145))
for name, file in [('Jony','arial.ttf'),('JonyBold','arialbd.ttf')]:
    pdfmetrics.registerFont(TTFont(name, 'C:/Windows/Fonts/' + file))
pdfmetrics.registerFontFamily('Jony',normal='Jony',bold='JonyBold')
BLUE, NAVY = colors.HexColor('#2162e8'), colors.HexColor('#10213b')
styles = {k:ParagraphStyle(k,fontName='JonyBold' if bold else 'Jony',fontSize=size,leading=size*1.45,textColor=color,spaceAfter=space,keepWithNext=k in ('h','sub')) for k,size,bold,color,space in [('title',25,True,NAVY,20),('h',15,True,NAVY,10),('sub',11,True,BLUE,7),('p',10,False,NAVY,7),('small',8,False,NAVY,5)]}

def p(text,style='p'):
    return Paragraph(escape(str(text)).replace('\n','<br/>'),styles[style])

def frame(c,doc):
    w,h=doc.pagesize
    c.saveState()
    c.drawImage(str(ROOT/'src/assets/brand-icon.png'),36,h-45,23,23,mask='auto')
    c.setFont('JonyBold',11); c.setFillColor(BLUE); c.drawString(70,h-37,'JONY / РУССКИЙ ЯЗЫК')
    pattern=ROOT/'public/student-design/pattern.png'
    if pattern.exists():
        for band in range(6): c.drawImage(str(pattern),36+band*(w-72)/6,h-58,(w-72)/6,(w-72)/6*690/8147,mask='auto')
    c.setStrokeColor(colors.HexColor('#dfe6f0')); c.line(36,34,w-36,34)
    c.setFont('Jony',8); c.setFillColor(NAVY); c.drawString(36,21,'1 yil · 144 dars · Haftasiga 3 × 120 daqiqa'); c.drawRightString(w-36,21,str(doc.page)); c.restoreState()

def save(name,story):
    SimpleDocTemplate(str(OUT/(name+'.pdf')),pagesize=A4,leftMargin=36,rightMargin=36,topMargin=72,bottomMargin=48,title='Jony Rus tili · '+name,author='Jony Academy').build(story,onFirstPage=frame,onLaterPages=frame)
    print(name)

def cover(title,subtitle,note):
    return [Spacer(1,40),p(title,'title'),p(subtitle,'h'),p(note),p('0 dan boshlanadigan, amaliy suhbatga yo‘naltirilgan mualliflik kursi.','small'),PageBreak()]

def table(rows,widths):
    t=Table([[p(cell,'small') for cell in row] for row in rows],colWidths=widths,repeatRows=1,hAlign='LEFT')
    t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#dbeafe')),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#f3f6fc')]),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),9),('RIGHTPADDING',(0,0),(-1,-1),9),('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7),('LINEBELOW',(0,0),(-1,0),1,BLUE)]))
    return t

months=['Ilk suhbat va talaffuz','Oila, sonlar va vaqt','Kundalik hayot','Xarid va kafe','Shahar va yo‘l','Voqealar va rejalar','Uy-joy va tanlov','Yordam va uchrashuvlar','Ish va o‘qish','Safar va muammolar','Fikr va hikoya','Mustaqil muloqot']
rubric='Har mezon 0–4: 0 — bajarmadi; 1 — ko‘p yordam bilan; 2 — qisman mustaqil; 3 — asosan mustaqil; 4 — erkin va vaziyatga mos. Ichki o‘tish mezoni: jami kamida 14/20, vazifani bajarish va tushunarli talaffuz har biri kamida 2. Yetmagan mezonni mashq qilib qayta tekshiring. Bu sertifikat bahosi emas.'
timeline=[('0–10','Eslash va uy vazifasi','Oldingi darsdan 3 ibora. Birinchi darsda xarita va tartib.'),('10–20','Talaffuz va 8 ibora','Namuna → birgalikda → individual; ma’noni vaziyatda tekshirish.'),('20–35','Grammatika','2 misol, qoida, 3 mashq va juftlikda tekshirish.'),('35–50','Tinglash','Dialogni ikki marta o‘qing; matnsiz 3 savol, keyin matn bilan tekshirish.'),('50–55','Tanaffus','Qisqa dam.'),('55–70','Dialog','A/B rollarni almashtirish; ism, joy, vaqtni o‘zgartirish.'),('70–95','Vaziyatli suhbat','Har kim faqat o‘z kartasini ko‘radi; sherikni almashtirish.'),('95–105','Yangi sharoit','Kutilmagan vaziyatga mos javob.'),('105–115','Yozish va uy vazifasi','Suhbatdan qisqa xabar; topshirish tartibini ko‘rsatish.'),('115–120','Chiqish tekshiruvi','Matnsiz darsga xos vazifa va bitta tavsiya.')]
story=cover('Rus tili\nKurs xaritasi','12 oy · 48 o‘quv haftasi · 288 soat','Haftasiga 3 ta 2 soatlik dars. Qolgan taqvim haftalari bayramlar, takrorlash va qayta tekshiruv uchun zaxira. Natija amaliy suhbat orqali oyma-oy tekshiriladi.')
story += [p('Har darsdagi tartib','h'),table([['VAQT','BOSQICH','USTOZ VAZIFASI']]+timeline,[65,135,323]),Spacer(1,14),p('Mustaqil ish','h'),p('Dars oralig‘ida 30–45 daqiqa tavsiya qilinadi: iborani eslash, ovozli mashq va qisqa yozish. Iboralarni 1, 3 va 7 kundan keyin qaytaring. Xatoni qayd etib, tuzatilgan gapni qayta ayting.'),p('Oylik suhbat bahosi','h'),p('5 mezon: vazifani bajarish; tushunarli talaffuz; savol-javob va tinglash; iboralar va so‘z tanlash; grammatik aniqlik.'),p(rubric),p('144-dars alohida yakuniy sinov: 4 bekat, har biri 15 ball. Jami 40/60, har bekatda 8/15 va vazifa natijasi 2/3; batafsil mezon 144-darsda.'),PageBreak()]
for m in range(1,13):
    story += [p(f'{m}-oy · {months[m-1]}','title'),p(f'{(m-1)*4+1}–{m*4}-hafta · 12 dars · 24 soat','sub')]
    story += [table([['DARS','MAVZU VA NATIJA']]+[[str(l['no']),l['title']+'\n'+l['objective']] for l in lessons if l['month']==m],[45,478]),PageBreak()]
save('jony-russian-course-map',story[:-1])

for month in range(1,13):
    pool=[l for l in lessons if l['month']==month]
    teacher=cover(f'{month}-oy\nUstoz qo‘llanmasi',months[month-1],'Tayyor dars rejasi, dialog, javoblar va baholash. Har uchinchi dars — yangi vaziyatga ko‘chirish; har o‘n ikkinchi dars — oylik suhbat nazorati.')
    teacher += [p('120 daqiqalik tartib','h'),table([['VAQT','BOSQICH','USTOZ VAZIFASI']]+timeline,[65,135,323]),p('Baholash','h'),p(rubric),p('144-dars alohida yakuniy sinov: 4 bekat, har biri 15 ball. Jami 40/60, har bekatda 8/15 va vazifa natijasi 2/3; batafsil mezon 144-darsda.'),PageBreak()]
    workbook=cover(f'{month}-oy\nSuhbat daftari',months[month-1],'Avval mustaqil bajaring. Tinglash matnini ustoz ikki marta o‘qiydi; dialogni savollardan keyin oching. Javoblar ustoz qo‘llanmasida. Ism: ______________________________')
    for l in pool:
        heading=f"{l['no']}-dars · {l['title']}"
        teacher += [p(heading,'title'),p(l['objective'],'sub'),p('Ustoz uchun','h'),p(l['teacherTip']),p('Grammatika · '+l['grammar']['title'],'h'),p(l['grammar']['rule'])]
        workbook += [p(heading,'title'),p(l['objective'],'sub'),p('Grammatika · '+l['grammar']['title'],'h'),p(l['grammar']['rule'])]
        for e in l['grammar']['examples']:
            teacher += [p(e['ru'],'sub'),p(e['uz'])]
            workbook += [p(e['ru'],'sub'),p(e['uz'])]
        teacher += [p('Mashq va javoblar','h')]
        workbook += [p('Mashq qiling','h')]
        for i,q in enumerate(l['grammar']['exercises'],1):
            teacher += [p(f"{i}. {q['prompt']}"),p(q['answer'],'sub'),p(q['explanation'],'small')]
            workbook += [p(f"{i}. {q['prompt']}"),p('Javob: __________________________________________________','small'),Spacer(1,6)]
        rows=[['RUSCHA IBORA','MA’NOSI']]+[[x['ru'],x['uz']] for x in l['phrases']]
        teacher += [p('8 ta ibora','h'),table(rows,[261,262]),Spacer(1,12),p('Tinglash dialogi','h')]
        workbook += [p('8 ta ibora · gapda ishlating','h'),table(rows,[261,262]),Spacer(1,12),p('Tinglang va javob bering','h')]
        for line in l['dialog']: teacher += [p(f"{line['speaker']}: {line['ru']}"),p(line['uz'],'small')]
        for i,q in enumerate(l['questions'],1):
            teacher += [p(f"{i}. {q['prompt']}"),p('Namuna: '+q['answer'],'sub')]
            workbook += [p(f"{i}. {q['prompt']}"),p('Javob: __________________________________________________','small'),Spacer(1,8)]
        for target in [teacher,workbook]:
            target += [p('Vaziyatli suhbat','h')]
            if target is teacher:
                target += [p('Ushbu sahifadagi A va B ma’lumotlarini alohida qog‘ozga ko‘chiring yoki kitob oxiridagi kartalarni kesib tarqating. Har o‘quvchi faqat o‘z rolini ko‘radi.','small'),p('A rol kartasi','sub'),p(l['roleplay']['a']),p('B rol kartasi','sub'),p(l['roleplay']['b']),p('Kutilmagan o‘zgarish','sub'),p(l['roleplay']['twist'])]
            else:
                target += [p('Ustozdan faqat A yoki B kartangizni oling. Undagi ma’lumotni sherigingizga ko‘rsatmang. Savol berib kerakli ma’lumotni aniqlang. Keyin rollarni almashtiring.'),p('Kelishuvimiz: ____________________________________________'),Spacer(1,12)]
            target += [p('Muvaffaqiyat mezoni','sub'),p(l['roleplay']['success']),p('Uyga vazifa','h')]
            target += [p(f'{i}. {h}') for i,h in enumerate(l['homework'],1)]
            target += [p('Chiqish tekshiruvi','h'),p(l['exit'])]
            if l['no']==144:
                target += [p('Yakuniy suhbat natijasi','h'),p('1-bekat: ___/15 · 2-bekat: ___/15 · 3-bekat: ___/15 · 4-bekat: ___/15'),p('Jami: ___/60 · Qayta tekshirish: _____________________'),p('40/60, har bekatda kamida 8/15 va vazifa natijasi 2/3. Batafsil mezon ustoz qo‘llanmasida.','small')]
            elif l['no']%12==0:
                target += [p('Oylik suhbat natijasi','h'),p('Vazifa: ___/4 · Talaffuz: ___/4 · Muloqot: ___/4 · Iboralar: ___/4 · Grammatika: ___/4'),p('Jami: ___/20 · Keyingi shaxsiy vazifa: _____________________'),p(rubric,'small')]
            target.append(PageBreak())
    workbook += [p('Dialoglar · tinglagandan keyin','title'),p('Savollarga javob bergach matn va tarjima orqali tekshiring.')]
    for l in pool:
        workbook.append(p(f"{l['no']}-dars",'h'))
        for line in l['dialog']: workbook += [p(f"{line['speaker']}: {line['ru']}"),p(line['uz'],'small')]
        workbook.append(Spacer(1,12))
    teacher += [p('Kesib tarqatiladigan rol kartalari','title'),p('Har dars uchun A va B kartani chiziq bo‘ylab ajrating. O‘quvchiga faqat o‘z kartasini bering. Kutilmagan vaziyatni suhbatning keyingi bosqichida og‘zaki ayting.'),PageBreak()]
    for l in pool:
        teacher += [p(f"{l['no']}-dars · A kartasi",'h'),p(l['roleplay']['a']),Spacer(1,80),p('- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -','small'),Spacer(1,30),p(f"{l['no']}-dars · B kartasi",'h'),p(l['roleplay']['b']),PageBreak()]
    save(f'jony-russian-month-{month}-teacher',teacher[:-1])
    save(f'jony-russian-month-{month}-workbook',workbook)
