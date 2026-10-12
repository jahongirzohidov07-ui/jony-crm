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
def load_lessons():
    """Merge teacher text only; fail before writing PDFs if any overlay is incomplete."""
    lessons = []
    for part in range(1, 5):
        source = json.loads((ROOT / f'src/data/russian/part-{part}.json').read_text(encoding='utf-8'))
        translated = json.loads((ROOT / f'src/data/russian/teacher-ru-{part}.json').read_text(encoding='utf-8'))
        if len(source) != len(translated):
            raise ValueError(f'Часть {part}: количество переводов не совпадает с количеством уроков')
        for lesson, translation in zip(source, translated):
            no = lesson['no']
            if translation['no'] != no:
                raise ValueError(f'Часть {part}: неверный номер перевода урока {no}')
            grammar = lesson['grammar']
            translated_grammar = translation['grammar']
            for label, original, overlay in (
                ('упражнений', grammar['exercises'], translated_grammar['exercises']),
                ('вопросов', lesson['questions'], translation['questions']),
                ('домашних заданий', lesson['homework'], translation['homework']),
            ):
                if len(original) != len(overlay):
                    raise ValueError(f'Урок {no}: количество {label} в переводе не совпадает с оригиналом')
            merged = dict(lesson)
            for field in ('title', 'objective', 'teacherTip', 'homework', 'exit'):
                merged[field] = translation[field]
            merged['roleplay'] = {field: translation['roleplay'][field] for field in ('a', 'b', 'twist', 'success')}
            merged['grammar'] = {
                **grammar,
                'title': translated_grammar['title'],
                'rule': translated_grammar['rule'],
                'exercises': [
                    {**original, 'prompt': overlay['prompt'], 'explanation': overlay['explanation']}
                    for original, overlay in zip(grammar['exercises'], translated_grammar['exercises'])
                ],
            }
            merged['questions'] = [
                {**original, 'prompt': overlay['prompt']}
                for original, overlay in zip(lesson['questions'], translation['questions'])
            ]
            lessons.append(merged)
    if [lesson['no'] for lesson in lessons] != list(range(1, 145)):
        raise ValueError('Ожидаются все 144 урока по порядку, без пропусков и повторений')
    return lessons


lessons = load_lessons()
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
    c.setFont('Jony',8); c.setFillColor(NAVY); c.drawString(36,21,'1 год · 144 урока · 3 занятия по 120 минут в неделю'); c.drawRightString(w-36,21,str(doc.page)); c.restoreState()

def save(name,story,title):
    OUT.mkdir(parents=True, exist_ok=True)
    SimpleDocTemplate(str(OUT/(name+'.pdf')),pagesize=A4,leftMargin=36,rightMargin=36,topMargin=72,bottomMargin=48,title='Русский язык · '+title,author='Академия Джони').build(story,onFirstPage=frame,onLaterPages=frame)
    print(name)

def cover(title,subtitle,note):
    return [Spacer(1,40),p(title,'title'),p(subtitle,'h'),p(note),p('Авторский курс с нуля с упором на практическое общение.','small'),PageBreak()]

def table(rows,widths):
    t=Table([[p(cell,'small') for cell in row] for row in rows],colWidths=widths,repeatRows=1,hAlign='LEFT')
    t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#dbeafe')),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#f3f6fc')]),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),9),('RIGHTPADDING',(0,0),(-1,-1),9),('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7),('LINEBELOW',(0,0),(-1,0),1,BLUE)]))
    return t

months=['Первый разговор и произношение','Семья, числа и время','Повседневная жизнь','Покупки и кафе','Город и маршруты','События и планы','Жильё и выбор','Помощь и встречи','Работа и учёба','Поездки и решение проблем','Мнения и рассказы','Самостоятельное общение']
rubric='Каждый критерий оценивается от 0 до 4: 0 — не выполнено; 1 — со значительной помощью; 2 — частично самостоятельно; 3 — в основном самостоятельно; 4 — свободно и с учётом ситуации. Внутренний проходной порог: не менее 14/20, при этом за выполнение задачи и понятность произношения — не менее 2 баллов по каждому критерию. Отработайте слабые критерии и проведите повторную проверку. Это не оценка сертификационного экзамена.'
timeline=[('0–10','Повторение и домашнее задание','Три фразы из прошлого урока. На первом уроке — карта курса и порядок работы.'),('10–20','Произношение и 8 фраз','Образец → хором → индивидуально; проверка понимания в ситуации.'),('20–35','Грамматика','Два примера, правило, три упражнения и проверка в парах.'),('35–50','Аудирование','Прочитайте диалог дважды; три вопроса без текста, затем проверка по тексту.'),('50–55','Перерыв','Короткий отдых.'),('55–70','Диалог','Поменяйте роли A/B; измените имя, место и время.'),('70–95','Ситуационный диалог','Каждый видит только свою карточку; смена партнёра.'),('95–105','Новые обстоятельства','Ответ с учётом неожиданного условия.'),('105–115','Письмо и домашнее задание','Короткое сообщение по итогам разговора; объясните порядок сдачи.'),('115–120','Проверка в конце урока','Итоговое задание урока без текста и одна рекомендация.')]
story=cover('Русский язык\nКарта курса','12 месяцев · 48 учебных недель · 288 часов','Три занятия в неделю по два часа. Оставшиеся календарные недели — резерв для праздников, повторения и повторной проверки. Каждый месяц результат проверяется в практическом разговоре.')
story += [p('Порядок работы на каждом уроке','h'),table([['ВРЕМЯ','ЭТАП','ЗАДАЧА ПРЕПОДАВАТЕЛЯ']]+timeline,[65,135,323]),Spacer(1,14),p('Самостоятельная работа','h'),p('Рекомендуется заниматься 30–45 минут между уроками: повторять фразы, выполнять устные упражнения и короткие письменные задания. Повторяйте фразы через 1, 3 и 7 дней. Отметьте ошибку и снова произнесите исправленное предложение.'),p('Ежемесячная оценка разговорной речи','h'),p('Пять критериев: выполнение задачи; понятность произношения; взаимодействие и понимание партнёра; фразы и выбор слов; грамматическая точность.'),p(rubric),p('Урок 144 — отдельное итоговое испытание: четыре станции по 15 баллов. Не менее 40/60 в сумме, не менее 8/15 на каждой станции и не менее 2/3 за результат задания; подробные критерии — в уроке 144.'),PageBreak()]
for m in range(1,13):
    story += [p(f'Месяц {m} · {months[m-1]}','title'),p(f'Недели {(m-1)*4+1}–{m*4} · 12 уроков · 24 часа','sub')]
    story += [table([['УРОК','ТЕМА И РЕЗУЛЬТАТ']]+[[str(l['no']),l['title']+'\n'+l['objective']] for l in lessons if l['month']==m],[45,478]),PageBreak()]
save('jony-russian-course-map',story[:-1],'Карта курса')

for month in range(1,13):
    pool=[l for l in lessons if l['month']==month]
    teacher=cover(f'Месяц {month}\nРуководство преподавателя',months[month-1],'Готовый план урока, диалог, ответы и оценивание. Каждый третий урок — применение изученного в новой ситуации; каждый двенадцатый — ежемесячная устная проверка.')
    teacher += [p('План занятия на 120 минут','h'),table([['ВРЕМЯ','ЭТАП','ЗАДАЧА ПРЕПОДАВАТЕЛЯ']]+timeline,[65,135,323]),p('Оценивание','h'),p(rubric),p('Урок 144 — отдельное итоговое испытание: четыре станции по 15 баллов. Не менее 40/60 в сумме, не менее 8/15 на каждой станции и не менее 2/3 за результат задания; подробные критерии — в уроке 144.'),PageBreak()]
    workbook=cover(f'Месяц {month}\nРабочая тетрадь по разговорной практике',months[month-1],'Сначала выполните задания самостоятельно. Преподаватель читает текст для аудирования дважды; открывайте диалог после ответов на вопросы. Ответы находятся в руководстве преподавателя. Имя: ______________________________')
    for l in pool:
        heading=f"Урок {l['no']} · {l['title']}"
        teacher += [p(heading,'title'),p(l['objective'],'sub'),p('Для преподавателя','h'),p(l['teacherTip']),p('Грамматика · '+l['grammar']['title'],'h'),p(l['grammar']['rule'])]
        workbook += [p(heading,'title'),p(l['objective'],'sub'),p('Грамматика · '+l['grammar']['title'],'h'),p(l['grammar']['rule'])]
        for e in l['grammar']['examples']:
            teacher += [p(e['ru'],'sub'),p('Перевод на узбекский: ' + e['uz'])]
            workbook += [p(e['ru'],'sub'),p('Перевод на узбекский: ' + e['uz'])]
        teacher += [p('Упражнения и ответы','h')]
        workbook += [p('Выполните упражнения','h')]
        for i,q in enumerate(l['grammar']['exercises'],1):
            teacher += [p(f"{i}. {q['prompt']}"),p(q['answer'],'sub'),p(q['explanation'],'small')]
            workbook += [p(f"{i}. {q['prompt']}"),p('Ответ: __________________________________________________','small'),Spacer(1,6)]
        rows=[['ФРАЗА НА РУССКОМ','ПЕРЕВОД НА УЗБЕКСКИЙ']]+[[x['ru'],x['uz']] for x in l['phrases']]
        teacher += [p('8 фраз','h'),table(rows,[261,262]),Spacer(1,12),p('Диалог для аудирования','h')]
        workbook += [p('8 фраз · используйте в предложении','h'),table(rows,[261,262]),Spacer(1,12),p('Послушайте и ответьте','h')]
        for line in l['dialog']: teacher += [p(f"{line['speaker']}: {line['ru']}"),p('Перевод на узбекский: ' + line['uz'],'small')]
        for i,q in enumerate(l['questions'],1):
            teacher += [p(f"{i}. {q['prompt']}"),p('Пример: '+q['answer'],'sub')]
            workbook += [p(f"{i}. {q['prompt']}"),p('Ответ: __________________________________________________','small'),Spacer(1,8)]
        for target in [teacher,workbook]:
            target += [p('Ситуационный диалог','h')]
            if target is teacher:
                target += [p('Перепишите сведения для ролей A и B с этой страницы на отдельные листы или вырежьте и раздайте карточки из конца книги. Каждый ученик видит только свою роль.','small'),p('Ролевая карточка A','sub'),p(l['roleplay']['a']),p('Ролевая карточка B','sub'),p(l['roleplay']['b']),p('Неожиданное изменение','sub'),p(l['roleplay']['twist'])]
            else:
                target += [p('Получите у преподавателя только свою карточку A или B. Не показывайте её партнёру. Задавайте вопросы, чтобы узнать нужную информацию. Затем поменяйтесь ролями.'),p('Наша договорённость: ____________________________________________'),Spacer(1,12)]
            target += [p('Критерий успеха','sub'),p(l['roleplay']['success']),p('Домашнее задание','h')]
            target += [p(f'{i}. {h}') for i,h in enumerate(l['homework'],1)]
            target += [p('Проверка в конце урока','h'),p(l['exit'])]
            if l['no']==144:
                target += [p('Результат итогового собеседования','h'),p('Станция 1: ___/15 · Станция 2: ___/15 · Станция 3: ___/15 · Станция 4: ___/15'),p('Всего: ___/60 · Повторная проверка: _____________________'),p('Не менее 40/60 в сумме, не менее 8/15 на каждой станции и не менее 2/3 за результат задания. Подробные критерии — в руководстве преподавателя.','small')]
            elif l['no']%12==0:
                target += [p('Результат ежемесячной устной проверки','h'),p('Задача: ___/4 · Произношение: ___/4 · Общение: ___/4 · Фразы: ___/4 · Грамматика: ___/4'),p('Всего: ___/20 · Следующее индивидуальное задание: _____________________'),p(rubric,'small')]
            target.append(PageBreak())
    workbook += [p('Диалоги · после прослушивания','title'),p('Ответив на вопросы, проверьте себя по тексту и переводу.')]
    for l in pool:
        workbook.append(p(f"Урок {l['no']}",'h'))
        for line in l['dialog']: workbook += [p(f"{line['speaker']}: {line['ru']}"),p('Перевод на узбекский: ' + line['uz'],'small')]
        workbook.append(Spacer(1,12))
    teacher += [p('Ролевые карточки для вырезания','title'),p('Разрежьте карточки A и B для каждого урока по пунктирной линии. Дайте каждому ученику только его карточку. Неожиданное условие сообщите устно на следующем этапе разговора.'),PageBreak()]
    for l in pool:
        teacher += [p(f"Урок {l['no']} · Карточка A",'h'),p(l['roleplay']['a']),Spacer(1,80),p('- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -','small'),Spacer(1,30),p(f"Урок {l['no']} · Карточка B",'h'),p(l['roleplay']['b']),PageBreak()]
    save(f'jony-russian-month-{month}-teacher',teacher[:-1],f'Месяц {month} · Руководство преподавателя')
    save(f'jony-russian-month-{month}-workbook',workbook,f'Месяц {month} · Рабочая тетрадь')
