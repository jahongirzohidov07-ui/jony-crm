/**
 * TIL: o'zbekcha (asosiy) va ruscha.
 *
 * 2026-08-13, Jahongir: "Profil bo'limida til o'zgartirish joyini
 * qo'shgin... hozir faqat rus tiliga o'tkiz, faqat ustozlar uchun shu
 * funksiyani ochib ber boshlanishiga".
 *
 * QANDAY ISHLAYDI. Interfeys matnlari kodda o'zbekcha yozilgan va ular
 * yuzlab joyda tarqalgan. Har bir faylni qayta yozish o'rniga —
 * lug'at: ekranga chiqqan o'zbekcha matn ruscha muqobiliga
 * almashtiriladi (translateDom). Lug'atda yo'q matn o'zbekcha
 * qolaveradi, ya'ni hech narsa buzilmaydi va lug'at asta to'ldirilib
 * boriladi.
 *
 * Hozircha faqat USTOZ kabinetida yoqilgan.
 */

export type UiLang = "uz" | "ru";

const KEY = "jonyos_ui_lang";

export function getUiLang(): UiLang {
  if (typeof localStorage === "undefined") return "uz";
  return localStorage.getItem(KEY) === "ru" ? "ru" : "uz";
}

export function setUiLang(l: UiLang) {
  try {
    localStorage.setItem(KEY, l);
  } catch {
    /* private rejimda yozib bo'lmaydi — muhim emas */
  }
}

/** Bitta matnni tarjima qilish (kerak bo'lsa qo'lda chaqirish uchun). */
export function t(uz: string): string {
  if (getUiLang() !== "ru") return uz;
  return RU[uz.trim()] || uz;
}

/** O'zbekcha -> ruscha. Kalit — ekranda ko'rinadigan matnning o'zi. */
export const RU: Record<string, string> = {
  // --- Qobiq va navigatsiya
  "Bugun": "Сегодня",
  "Jadval": "Расписание",
  "Bo'limlar": "Разделы",
  "Profil": "Профиль",
  "Jony Teacher": "Jony Teacher",
  "Barcha funksiyalaringiz": "Все ваши функции",
  "Barcha funksiyalar": "Все функции",
  "Kundalik ish": "Ежедневная работа",
  "Buyurtmalar": "Заказы",
  "Natijalar va oylik": "Результаты и зарплата",
  "Boshqa": "Прочее",
  "Chiqish": "Выйти",
  "To'liq panelga o'tish": "Перейти в полную панель",
  "Kompyuter ko'rinishi (JonyOS)": "Версия для компьютера (JonyOS)",
  "Lavozim": "Должность",
  "Qaysi lavozimda ishlashni tanlang — panel to'liq o'zgaradi":
    "Выберите, в какой должности работать — панель полностью изменится",
  "Til": "Язык",
  "O'zbekcha": "O‘zbekcha",
  "Ruscha": "Русский",

  // --- Bo'limlar ro'yxati
  "Guruhlarim": "Мои группы",
  "Davomat, baholash, imtihonlar": "Посещаемость, оценки, экзамены",
  "O'quvchilarim": "Мои ученики",
  "Barcha o'quvchilaringiz ro'yxati": "Список всех ваших учеников",
  "Dars jadvalim": "Моё расписание",
  "Darslarim": "Мои уроки",
  "To'liq jadval va ko'chirishlar": "Полное расписание и переносы",
  "Umumiy jadval": "Общее расписание",
  "Markazning dars jadvali": "Расписание центра",
  "Kitob buyurtma": "Заказ книг",
  "Kitob buyurtmasi": "Заказ книги",
  "O'quvchilaringiz uchun kitob": "Книги для ваших учеников",
  "Imtihon buyurtma": "Заказ экзамена",
  "Imtihon buyurtmasi": "Заказ экзамена",
  "Unit / mock test so'rash": "Запрос юнита / mock-теста",
  "Lug'at unitlari": "Юниты словаря",
  "Unit topshirganini tasdiqlash (100%)": "Подтверждение сдачи юнита (100%)",
  "Soat belgilash": "Отметить часы",
  "Support seanslarini yozish": "Запись сессий саппорта",
  "Darslarim va oyligim": "Мои уроки и зарплата",
  "Ishlab topganim va balans": "Заработанное и баланс",
  "Mening natijalarim": "Мои результаты",
  "Guruhlaringiz o'zlashtirishi": "Успеваемость ваших групп",
  "Karyera yo'lim": "Мой карьерный путь",
  "Daraja va o'sish rejasi": "Уровень и план роста",
  "Gamifikatsiya": "Геймификация",
  "O'quvchilar XP va ligalari": "XP и лиги учеников",
  "Vazifalar": "Задачи",
  "Sizga berilgan topshiriqlar": "Порученные вам задания",
  "Murojaatlar": "Обращения",
  "Shikoyat va takliflar": "Жалобы и предложения",
  "Shaxsiy ma'lumotlar": "Личные данные",
  "Parolni o'zgartirish, telefon raqami": "Смена пароля, номер телефона",
  "Mening yo'lim": "Мой путь",
  "Hozirgi darajangiz": "Ваш текущий уровень",

  // --- Bugun / dars
  "Bugungi guruhlarim": "Мои группы на сегодня",
  "Bugungi darslar": "Уроки на сегодня",
  "Bugun darsingiz yo'q": "Сегодня у вас нет уроков",
  "Yo'qlama": "Посещаемость",
  "Yo'qlama qo'yilmagan darslar": "Уроки без отметки посещаемости",
  "Oyligingiz shu yo'qlamadan hisoblanadi":
    "Ваша зарплата считается по этой посещаемости",
  "Hammasi keldi": "Все пришли",
  "Keldi": "Пришёл",
  "Kelmadi": "Не пришёл",
  "Kechikdi": "Опоздал",
  "Uy vazifasi": "Домашнее задание",
  "Uy vazifasi va baho": "Домашнее задание и оценка",
  "Baho": "Оценка",
  "O'rtacha baho": "Средняя оценка",
  "Davomat": "Посещаемость",
  "Guruh": "Группа",
  "Guruhda o'quvchi yo'q": "В группе нет учеников",
  "Bu guruhda faol o'quvchi yo'q.": "В этой группе нет активных учеников.",
  "Sizga hali guruh biriktirilmagan.": "Вам пока не назначена группа.",
  "Haftalik jadval": "Расписание на неделю",
  "dars yo'q": "нет уроков",
  "bugun": "сегодня",
  "Dars ko'chirish": "Перенос урока",
  "Darsni ko'chirish va o'rinbosar ustoz": "Перенос урока и замещающий преподаватель",
  "Darsni boshqa kunga ko'chirish": "Перенести урок на другой день",
  "O'rinbosar": "Замещающий",
  "Shu oyda qoldi": "Осталось в этом месяце",
  "Kelasi oyda qoldi": "Останется в следующем месяце",
  "Kvotangiz tugagan — so'rov tasdiqqa yuboriladi.":
    "Ваша квота исчерпана — запрос уйдёт на утверждение.",
  "Ochiq takliflar — o'ta olasizmi?": "Открытые предложения — сможете провести?",
  "Hozircha ochiq taklif yo'q.": "Пока открытых предложений нет.",
  "Menga taklif qilinganlar": "Предложенные мне",
  "Sizga taklif yo'q.": "Для вас предложений нет.",
  "Mening so'rovlarim": "Мои запросы",
  "Siz hali o'rinbosar so'ramagansiz.": "Вы ещё не запрашивали замену.",
  "Eng ko'p surish": "Максимум переносов",
  "6 oyda ishlatilgan": "Использовано за 6 месяцев",

  // --- Support
  "Support davomati": "Посещаемость саппорта",
  "Support yo'qlamasi": "Отметка саппорта",
  "Support yo'qlamasi saqlandi": "Отметка саппорта сохранена",
  "O'quvchilarni belgilang, soatni tanlang": "Отметьте учеников, выберите часы",
  "Necha soat dars o'tdingiz": "Сколько часов вы провели",
  "Bugungi seansingizni yozing — oylik shundan":
    "Запишите сегодняшнюю сессию — зарплата считается по ней",
  "Kun": "День",
  "Boshlanish vaqti": "Время начала",
  "Sana": "Дата",
  "Vaqt": "Время",
  "Soni": "Количество",
  "Daraja": "Уровень",
  "O'quvchi soni *": "Количество учеников *",
  "Kitob nomi *": "Название книги *",
  "omborda yo'q": "нет на складе",

  // --- Umumiy tugma va holatlar
  "Saqlash": "Сохранить",
  "Saqlanmoqda...": "Сохраняется...",
  "Saqlanmoqda…": "Сохраняется…",
  "Saqlandi": "Сохранено",
  "Saqlangan": "Сохранено",
  "Yuborish": "Отправить",
  "Bekor": "Отмена",
  "Bekor qilish": "Отменить",
  "Tasdiqni bekor qilish": "Отменить подтверждение",
  "O'chirish": "Удалить",
  "Qayta urinish": "Повторить",
  "Yuklanmoqda...": "Загрузка...",
  "Yuklanmoqda…": "Загрузка…",
  "Yuklab bo'lmadi": "Не удалось загрузить",
  "Ro'yxatni yuklab bo'lmadi": "Не удалось загрузить список",
  "Xatolik": "Ошибка",
  "Izoh": "Комментарий",
  "Izoh (ixtiyoriy)": "Комментарий (необязательно)",
  "Sabab": "Причина",
  "Sababni tanlang": "Выберите причину",
  "Sababi (ixtiyoriy)": "Причина (необязательно)",
  "Rad etish": "Отклонить",
  "Rad etish sababi?": "Причина отклонения?",
  "Yangi buyurtma": "Новый заказ",
  "Guruhni tanlang": "Выберите группу",
  "O'quvchini tanlang": "Выберите ученика",
  "Ism bo'yicha qidirish…": "Поиск по имени…",
  "O'quvchi topilmadi.": "Ученик не найден.",
  "Yozuv yo'q.": "Записей нет.",
  "Hozircha yo'q": "Пока нет",
  "Kutayotgan so'rov yo'q.": "Ожидающих запросов нет.",
  "So'rov bekor qilinsinmi?": "Отменить запрос?",
  "hammasini ko'rish": "показать все",
  "ularni ko'rish": "показать их",
  "Oldingi oy": "Прошлый месяц",
  "Keyingi oy": "Следующий месяц",
  "Barcha guruhlarim": "Все мои группы",
  "O'quvchi": "Ученик",
  "O'quvchilar": "Ученики",
  "O'qituvchi": "Преподаватель",
  "Support teacher": "Саппорт-преподаватель",
  "Topshirdi": "Сдал",
  "Kutubxona": "Библиотека",
  "Imtihon": "Экзамен",
  "Coin": "Коин",
  "Coin ayirish (intizom, 1–15)": "Списать коины (дисциплина, 1–15)",
  "1–15 ta": "1–15 шт",
  "sinov": "пробный",
  "Qancha vaqt": "Сколько времени",

  // --- Oylik va natijalar
  "Ishlab topgan": "Заработано",
  "Olgan": "Получено",
  "Balans": "Баланс",
  "Faol o'quvchilar": "Активные ученики",
  "To'lov yig'ildi": "Собрано оплат",
  "Yangi mijozlar": "Новые клиенты",
  "Jami bonus": "Итого бонус",
  "bonus yo'q": "бонуса нет",
  "Shu oy soat": "Часы за месяц",
  "Hisoblangan": "Начислено",
  "oylik yo'q": "зарплаты нет",
  "Oylik qanday hisoblanadi": "Как считается зарплата",
  "O'qish rejasi": "План обучения",
  "Tarix": "История",
  "Bu oy dars": "Уроков за месяц",
  "Hozir o'qiyapti": "Сейчас учится",
  "Ketgan": "Ушёл",
  "Qolish foizi": "Процент удержания",
  "Ketish foizi": "Процент оттока",
  "O'rtacha qancha oy o'qiydi": "Сколько месяцев в среднем учится",
  "O'quvchi qancha qoladi": "Сколько ученик остаётся",
  "Mening natijam": "Мой результат",
  "Coin do'koni": "Магазин коинов",
  "Sovg'alar": "Подарки",
  "Coin tarixi": "История коинов",
  "Daraja yo'li": "Путь уровней",
  "noma'lum": "неизвестно",
  "Yo'q": "Нет",

  // --- Hafta kunlari
  "Dushanba": "Понедельник",
  "Seshanba": "Вторник",
  "Chorshanba": "Среда",
  "Payshanba": "Четверг",
  "Juma": "Пятница",
  "Shanba": "Суббота",
  "Yakshanba": "Воскресенье",
  "Du": "Пн", "Se": "Вт", "Chor": "Ср", "Pay": "Чт",
  "Ju": "Пт", "Shan": "Сб", "Yak": "Вс",

  // --- Oylar
  "Yanvar": "Январь", "Fevral": "Февраль", "Mart": "Март",
  "Aprel": "Апрель", "May": "Май", "Iyun": "Июнь", "Iyul": "Июль",
  "Avgust": "Август", "Sentabr": "Сентябрь", "Oktabr": "Октябрь",
  "Noyabr": "Ноябрь", "Dekabr": "Декабрь",
  "Yan": "Янв", "Fev": "Фев", "Mar": "Мар", "Apr": "Апр",
  "Avg": "Авг", "Sen": "Сен", "Okt": "Окт", "Noy": "Ноя", "Dek": "Дек",

  // --- Qisqa birliklar
  "so'm": "сум",
  "dona": "шт",
  "kun": "дней",
  "dars": "урок",
  "ta": "шт",
};

const ATTRS = ["placeholder", "title", "aria-label", "alt"];

/** Sahifadagi matnlarni lug'at bo'yicha ruschaga o'giradi. */
export function translateDom(root: ParentNode = document.body) {
  if (getUiLang() !== "ru") return;
  const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
  const nodes: Text[] = [];
  let n: Node | null;
  while ((n = walker.nextNode())) nodes.push(n as Text);
  for (const node of nodes) {
    const raw = node.nodeValue || "";
    const key = raw.trim();
    if (!key) continue;
    const ru = RU[key];
    if (ru && ru !== key) {
      node.nodeValue = raw.replace(key, ru);
    }
  }
  const els = (root as Element).querySelectorAll?.("[placeholder],[title],[aria-label],[alt]");
  els?.forEach((el) => {
    for (const a of ATTRS) {
      const v = el.getAttribute(a);
      if (v && RU[v.trim()]) el.setAttribute(a, RU[v.trim()]);
    }
  });
}
