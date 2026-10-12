# Rus tili — bir yillik suhbat kursi

## Dastur

0 dan boshlanadi. Haftasiga 3 × 120 daqiqa. 48 o‘quv haftasi, 144 dars,
288 soat. 12 ta o‘quv bloki — har birida 12 dars. Yillik taqvimdagi
qolgan haftalar bayram, takrorlash va qayta tekshirish uchun ajratiladi.
Har uchinchi dars oldingi bilimlarni yangi vaziyatda ishlatadi;
har 12-dars oylik og‘zaki tekshiruv bilan yakunlanadi.

`/plans/russian` sahifasi ustoz uchun; `?lesson=37` tanlangan darsga olib boradi.
`/russian-placement` (qisqa manzil `/rus-test`) kirish testi uchun.
Kurs CEFR sertifikati yoki kafolatlangan daraja sifatida taqdim qilinmaydi.

## Materiallar

Yagona manba — `src/data/russian/part-1.json` … `part-4.json`.
Har darsda maqsad, grammatika qoidasi va ikki misol, uchta javobli mashq,
sakkizta ruscha-o‘zbekcha ibora, 6/8 replikali dialog, uchta tushunish
savoli, ikki rol kartasi, kutilmagan vaziyat, ustoz ko‘rsatmasi,
uchta uy vazifasi va yakuniy tekshiruv bor.
1152 — iboralarning darslardagi o‘rinlari soni; takroriy iboralar ham mavjud.

Tinglash: ustoz o‘qiydi yoki qurilmadagi ruscha sintetik ovoz ishlatiladi.
Ovoz bo‘lmasa, boshqa tildagi ovozga almashtirilmaydi.
Audio yozuv to‘plami taqdim qilinmaydi. Uy vazifalarini qabul qilish kanali
ustoz tomonidan belgilanadi. Darsdagi oddiy mashq natijalari rasmiy baho emas.

## Baholash

Oylik og‘zaki mezonlar: vazifani bajarish, talaffuz, sherik bilan muloqot,
iboralar va grammatik aniqlik — har biri 0–4 ball.
Ichki o‘tish: 14/20, vazifa va talaffuz kamida 2 balldan.
Past mezon uchun qayta mashq va qayta tekshiruv.
144-dars alohida yakuniy sinov: 4 bekat × 15 ball. Jami kamida 40/60,
har bekatda kamida 8/15 va vazifa natijasi kamida 2/3.
Og‘zaki baholar bu dars qo‘llanmasida avtomatik saqlanmaydi.

## PDF va tekshiruv

`scripts/build-russian-pdfs.py` sayt bilan bir xil JSONdan 25 ta PDF yaratadi:
bitta kurs xaritasi, 12 ta ustoz qo‘llanmasi, 12 ta o‘quvchi daftari.
ReportLab va Windows Arial shriftlari ishlatiladi. Javoblar ustoz kitobida;
o‘quvchi daftaridagi dialoglar tinglash topshiriqlaridan keyin joylashgan.

`python -X utf8 scripts/test-russian-course.py` ma’lumotlar yaxlitligini
va barcha oylar uchun PDFlar mavjudligini tekshiradi.
PDFlarni ko‘z bilan tekshirish va TypeScript/build tekshiruvlari ham zarur.

PDFlar `public/russian/` ichida statik fayl sifatida xizmat qiladi va
Vercel Python funksiyasi paketidan chiqarib tashlangan.

## Kirish testi

48 savol: 6 ta ikki oylik blok, har birida 4 grammatika, 2 lug‘at,
2 o‘qib tushunish savoli. To‘rtta variant va alohida “Bilmayman” (-1)
bor. Birinchi o‘zlashtirilmagan blok tavsiya qilinadi: 1/25/49/73/97/121-dars.
Blok mezoni: kamida 6/8, grammatika kamida 3/4, o‘qish kamida 1/2.
Barcha bloklar o‘tilsa, yakuniy og‘zaki tekshiruv tavsiya qilinadi.
Bu tanlangan filial va kurs bosqichi tavsiyasi; haqiqiy guruhni ustoz
suhbatdan keyin tanlaydi. Natija avtomatik guruhga biriktirmaydi.

To‘g‘ri javoblar brauzerga yuborilmaydi; hisoblash serverda bajariladi.
Ism + telefon + filial mosligi bo‘yicha lid topiladi yoki yaratiladi.
Bir telefonni ishlatadigan turli ismli aka-ukalar birlashtirilmaydi.
Bir urinishni qayta yuborish natija va izohni takrorlamaydi.
Natijalar Lidlar sahifasidagi “Rus tili testi natijalari”da ochiladi;
filial chegaralari serverda tekshiriladi.

API, UI va sxema ishga tushishini tekshiradigan fayllar:
- `scripts/test-russian-placement-api.py`
- `scripts/test-russian-placement-ui.cjs`
- `scripts/test-russian-placement-schema.py`

Ingliz testi va Student Level Testga “Bilmayman” qo‘shildi. Nemis testidagi
mavjud beshinchi variant A–E belgisi va 0 ball tushuntirishi bilan aniqlandi.
Ingliz testining manfiy indeks orqali oxirgi javobga ball berish xatosi tuzatildi.


## Русскоязычная версия для преподавателей

Страница `/plans/russian`, карта курса, 12 методических пособий и 12 рабочих тетрадей используют русские инструкции. Перевод целей, правил, заданий, ролей, домашних работ и критериев находится в `src/data/russian/teacher-ru-1.json` … `teacher-ru-4.json`. Он накладывается на исходные уроки через `src/lib/russianTeacher.ts` и сборщик PDF. Нумерация, ответы, русские реплики и узбекские переводы для учеников остаются в исходных файлах `part-*.json`.

Приложение Jony Student продолжает получать исходные двуязычные материалы: перевод для преподавателей не меняет сохранённые результаты и ответы учеников. При изменении исходного урока обновляйте соответствующий перевод, затем пересобирайте PDF. Проверка перевода: `python -X utf8 scripts/test-russian-teacher.py`; проверка готовых PDF: тот же скрипт с `--pdf` (нужен PyMuPDF).
