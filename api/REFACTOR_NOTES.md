# main.py bo'linishi (2026-08)

## Nima o'zgardi

`api/main.py` 27 205 qator / 1.05 MB bitta faylda edi (478 ta HTTP route +
~290 ta yordamchi funksiya). Endi domen bo'yicha 26 ta faylga bo'lingan:

academic, audit_admin, auth_users, branches_rooms, complaints, content,
dashboard, examiners, exams, finance, gamification, groups_lessons, hr,
hr_ats, inventory, leads, marketing, me, notifications, parents, students,
support, system, tasks, teachers, timetable — har biri o'z `router =
APIRouter()` bilan.

Ko'p domenga tegishli yoki eng ko'p chaqiriladigan yordamchi funksiyalar
`common.py`ga tushdi (142 ta nom, `__all__` orqali eksport qilingan — muhim,
chunki `from common import *` `_` bilan boshlanadigan nomlarni `__all__`siz
olib kelmaydi).

Yangi `main.py` (161 qator) faqat: FastAPI ilovasini yaratadi, CORS o'rnatadi,
26 ta routerni `include_router()` bilan ulaydi, 3 ta seed-blok va xato
handlerini o'z ichiga oladi. **Business-logika bir qatori ham o'zgartirilmadi**
— faqat qayerda joylashgani o'zgardi (Python `ast` moduli orqali original
manba matnidan aniq chiqarib olindi).

Original fayl **o'chirilmadi** — `api/main_original.py` sifatida saqlanadi
(rollback kerak bo'lsa, `git mv main.py main_split_backup.py && git mv
main_original.py main.py`).

## entry.py'ga tuzatish

`entry.py`dagi `_drop_route()` funksiyasi `app.router.routes`ni tekis
(flat) ro'yxat deb kutadi. Bo'lingandan keyin routerlar
`app.include_router()` orqali ulanganda, FastAPI ularni ichma-ich
(`_IncludedRouter`) saqlaydi — shuning uchun `_drop_route` mos yo'lni
topolmay, "_v2" bilan almashtirilishi kerak bo'lgan 13 ta eski route
o'chmay qolar edi (aniqlab, tuzatib, tekshirilgan). Endi `_drop_route`
ichkariga ham qarab qidiradi — xatti-harakat asl holatiga to'liq mos.

## Tekshirilgan narsalar (barchasi o'tdi)

- **Route parity**: original va yangi versiyalarda ro'yxatdan o'tgan
  (method, path) juftliklari **bir xil — 525 ta, 0 farq** (entry.py'ning
  "_v2" almashtirishlaridan keyingi yakuniy holat, ikkala versiyada ham).
- **Aniqlanmagan nomlar**: barcha 26 fayl + common.py pyflakes orqali
  tekshirildi (wildcard import vaqtincha ochiq import qilib) — 0 ta xato.
  Yo'q edi: `json` importi 7 faylda, `teacher_career`/`admin_kpi`/
  `marketing_rfm` kabi bir routerdan ikkinchisini to'g'ridan-to'g'ri
  chaqiruvchi holatlar — barchasi tuzatildi.
- **entry.py va test fayllaridagi `main.xxx` / `M.xxx` murojaatlari**:
  hammasi (37+ nom) qayta eksport qilingan, endi ishlaydi.
- **Mavjud test to'plami** (`test_account`, `test_brand`, `test_hr_core`,
  `test_inbox`, `test_myresults`, `test_plan`): **hammasi o'tdi**.
  `test_staff_access.py` va `test_teacher_cabinet.py`da original
  main.py'da HAM bor bo'lgan, bo'linishga bog'liq bo'lmagan 2 ta muammo
  bor (frontend fayli topilmasligi va oldindan mavjud kvota-hisoblash
  xatosi) — ikkalasi ham original main.py bilan aynan takrorlanadi,
  demak bu bo'linish tufayli paydo bo'lgan emas.

## Agar davom ettirilsa (keyingi qadam, hali qilinmagan)

`entry.py`dagi ~59 ta "_v2" endpoint hali ham asl (main.py'dan ko'chgan)
versiya bilan yonma-yon turibdi ("_v2" ishlaydigan, eskisi drop qilingan).
Bularni tozalash — ya'ni asl route domain faylidan butunlay olib
tashlash — alohida, ehtiyotkorlik bilan qilinishi kerak bo'lgan keyingi
qadam (audit hisobotining shu bandi).
