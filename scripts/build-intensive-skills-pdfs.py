"""Print the same authored skill packs used by the application, one booklet per month."""
import json
import argparse
from pathlib import Path
from xml.sax.saxutils import escape
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, KeepTogether

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'public/intensive'
PACKS = json.loads((ROOT / 'src/data/intensive-skills.json').read_text(encoding='utf-8'))
OUTCOMES = json.loads((ROOT / 'src/data/intensive-month-outcomes.json').read_text(encoding='utf-8'))
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--months', nargs='+', type=int, choices=range(1,9), default=list(range(1,9)))
MONTHS = parser.parse_args().months
if set(MONTHS) == set(range(1,9)):
    assert len(PACKS) == 192 and [p['lesson'] for p in PACKS] == list(range(1,193))
for name, font in [('Jony', 'arial.ttf'), ('JonyBold', 'arialbd.ttf')]:
    pdfmetrics.registerFont(TTFont(name, 'C:/Windows/Fonts/' + font))
NAVY = colors.HexColor('#10213B')
BLUE = colors.HexColor('#2162E8')
STYLES = {name: ParagraphStyle(name, fontName='JonyBold' if bold else 'Jony', fontSize=size,
          leading=size*1.5, textColor=BLUE if name=='label' else NAVY, spaceAfter=gap)
          for name,size,bold,gap in [('title',25,True,18),('heading',16,True,12),('label',10,True,8),('body',10,False,9),('small',8.5,False,6)]}

def p(text, style='body'):
    return Paragraph(escape(str(text)).replace('\n', '<br/>'), STYLES[style])

def frame(canvas, doc):
    canvas.saveState()
    canvas.drawImage(str(ROOT/'src/assets/brand-icon.png'), 36, 800, 22, 22, mask='auto')
    canvas.setFillColor(NAVY); canvas.setFont('JonyBold', 10)
    canvas.drawString(68, 806, 'JONY INTENSIVE / FOUR SKILLS')
    for band in range(6): canvas.drawImage(str(ROOT/'public/student-design/pattern.png'),36+band*523/6,785,523/6,523/6*690/8147,mask='auto')
    canvas.setStrokeColor(colors.HexColor('#DFE6F0')); canvas.line(36, 34, 559, 34)
    canvas.setFont('Jony', 8); canvas.drawString(36, 20, 'O‘qi → tingla → fikr bildir → yoz → tekshir')
    canvas.drawRightString(559, 20, str(doc.page)); canvas.restoreState()

for month in MONTHS:
    packs = [p for p in PACKS if (month-1)*24 < p['lesson'] <= month*24]
    assert [p['lesson'] for p in packs] == list(range((month-1)*24+1,month*24+1)), 'Month incomplete'
    outcome = OUTCOMES[month-1]
    story = [Spacer(1,35),p(f'{month}-oy / 4 ko‘nikma', 'title'),p(outcome['focus'], 'heading'),
             p(f"{packs[0]['lesson']}–{packs[-1]['lesson']}-darslar · 24 reading · 24 listening · 48 ijodiy topshiriq", 'label'),
             p('Ism: ___________________________________\nGuruh: __________________________________'),
             p('Avval o‘quvchi sahifalari. Listening transkriptlari, javoblar va yozuv namunalari kitob oxiridagi ustoz bo‘limida. Ularni mashqdan oldin ochmang.'),
             p('Tinglash: saytdagi ovoz tugmasi yoki ustozning ikki marta tabiiy o‘qishi. Birinchi tinglashda mazmun, ikkinchisida tafsilotlar.'),
             p('Oy yakunidagi natijalar', 'heading')]
    story += [p('• '+item) for item in outcome['canDo']]
    story += [p(outcome['check']),p('Bu Jony ichki mashq kitobi. Daraja belgisi o‘quv maqsadini bildiradi; natijalar milliy sertifikat bali o‘rnini bosmaydi.', 'small'),PageBreak()]
    for pack in packs:
        story += [p(f"{pack['lesson']}-dars / Reading", 'heading'),p(pack['objective'],'label'),p(pack['reading']['title'],'heading'),p(pack['reading']['text'])]
        for i,q in enumerate(pack['reading']['questions'],1):
            story += [KeepTogether([p(f'{i}. {q["prompt"]}'),p('Javob: __________________________________________________','small')])]
        story += [p('Tekshiruv: javobni tasdiqlovchi joyni matnda belgilang. Noto‘g‘ri javob sababini bir gap bilan ayting.','small'),PageBreak(),
                  p(f"{pack['lesson']}-dars / Listening & production", 'heading'),p(pack['listening']['title'],'label'),
                  p('Transkript yopiq. Ustozni yoki saytdagi ovozni ikki marta tinglang.','small')]
        for i,q in enumerate(pack['listening']['questions'],1):
            story += [KeepTogether([p(f'{i}. {q["prompt"]}'),p('Javob: __________________________________________________','small')])]
        for mode,title in [('speaking','Speaking'),('writing','Writing')]:
            story += [p(title,'heading'),p(pack[mode]['prompt'])]
            story += [p('□ '+criterion,'small') for criterion in pack[mode]['success']]
        story += [p('Yozma ishni daftarga bajaring. Xato → to‘g‘ri shakl → sabab:','small'),p('__________________________________________________________\n__________________________________________________________','small'),PageBreak()]
    story += [p('USTOZ BO‘LIMI', 'title'),p('Transkriptlar, dalilli javoblar va yozuv namunalari','heading'),
              p('Speaking va writing uchun ichki mezonlar: vazifani bajarish, izchillik, lug‘at, grammar. Har biri 0 — hali bajarmadi; 1 — yordam bilan; 2 — mustaqil. 6/8 dan past yoki bir mezon 0 bo‘lsa, shu bandni qayta mashq qildiring. Erkin topshiriqda namunadan boshqa to‘g‘ri javoblar ham bo‘ladi.'),PageBreak()]
    for pack in packs:
        story += [p(f"{pack['lesson']}-dars / Ustoz kaliti",'heading'),p(pack['teacherNote'],'small'),p('Listening transkripti','label'),p(pack['listening']['text'])]
        for mode in ['reading','listening']:
            story += [p(mode.title()+' javoblari','label')]
            for i,q in enumerate(pack[mode]['questions'],1):
                story += [p(f"{i}. {' / '.join(q['answers'])} — {q['explanation']}",'small')]
        story += [p('Writing namunasi','label'),p(pack['writing']['model'],'small'),PageBreak()]
    file = OUT / f'jony-intensive-month-{month}-skills.pdf'
    SimpleDocTemplate(str(file),pagesize=A4,leftMargin=36,rightMargin=36,topMargin=65,bottomMargin=49,
                      title=f'Jony Intensive · {month}-oy · To‘rt ko‘nikma',author='Jony Academy').build(story[:-1],onFirstPage=frame,onLaterPages=frame)
    print(file.name)
