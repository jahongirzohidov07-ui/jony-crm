/**
 * IMTIHON BO'LIMLARI XARITASI (2026-08-26).
 *
 * Jahongir: "Yoq yanada alohida qil, IELTS va CEFR alohida tursin
 * SAT ham alohida tursin, keyin IELTSga kirganda Reading listening
 * writing speaking, tursin CEFR ga kirganda ham shunaqa CEFR
 * Reading, listening writing speaking tursin".
 *
 * TUZILMA. Ikki qavat:
 *   1-qavat  /student/ielts            -> IELTS | CEFR | SAT
 *   2-qavat  /student/ielts/exam/:key  -> Listening / Reading /
 *                                          Writing / Speaking
 *
 * NEGA alohida fayl (.ts, .tsx emas): ikkala ekran ham shu
 * ro'yxatni o'qiydi. Bitta manba bo'lsa, yangi imtihon qo'shish
 * uchun faqat shu yerga yozish kifoya.
 *
 * SAT haqida. SAT'da Listening va Speaking YO'Q - haqiqiy raqamli
 * SAT ikki moduldan iborat: "Reading and Writing" va "Math".
 * Yo'q narsani bor qilib ko'rsatmaymiz, shuning uchun SAT kartasi
 * o'z tuzilmasi bilan turadi.
 */

export type ExamKey = "ielts" | "cefr" | "sat";

/** api: shu kartaning mashq soni qaysi endpointdan olinadi. */
export type SkillCard = {
  key: string;
  title: string;
  desc: string;
  icon: string;
  href?: string;
  hint?: string;
  api?: "listening" | "reading";
};

export type ExamDef = {
  key: ExamKey;
  title: string;
  tag: string;
  desc: string;
  icon: string;
  ready: boolean;
  skills: SkillCard[];
};

export const EXAMS: ExamDef[] = [
  {
    key: "ielts",
    title: "IELTS",
    tag: "Academic",
    desc: "4 ko'nikma · 2 soat 45 daqiqa · 0-9 ball. Britaniya, "
      + "Kanada va Avstraliya universitetlari uchun.",
    icon: "/jsicons/learn-exam.png",
    ready: true,
    skills: [
      {
        key: "listening",
        title: "Listening",
        desc: "4 qism · 40 savol · 30 daqiqa. Suhbat, monolog va "
          + "ma'ruza — barchasi bir marta eshittiriladi.",
        icon: "/jsicons/learn-listening.png",
        href: "/student/ielts/listening?exam=ielts",
        api: "listening",
        hint: "Ism yozish, raqamlar, postcode va so'z tuzoqlari",
      },
      {
        key: "reading",
        title: "Reading",
        desc: "3 matn · 40 savol · 60 daqiqa. T/F/NG, sarlavha "
          + "moslash, jadval va gap to'ldirish.",
        icon: "/jsicons/learn-reading.png",
        href: "/student/ielts/reading?exam=ielts",
        api: "reading",
        hint: "14 savol turi",
      },
      {
        key: "writing",
        title: "Writing",
        desc: "Task 1 (grafik yoki jadval tavsifi, 150 so'z) va "
          + "Task 2 (esse, 250 so'z) · 60 daqiqa.",
        icon: "/jsicons/learn-writing.png",
      },
      {
        key: "speaking",
        title: "Speaking",
        desc: "3 qism · 11-14 daqiqa. Tanishuv, mavzu kartasi "
          + "(cue card) va munozara.",
        icon: "/jsicons/learn-jony-teacher.png",
      },
    ],
  },
  {
    key: "cefr",
    title: "CEFR Multilevel",
    tag: "A1-C2",
    desc: "4 ko'nikma · daraja bilan baholanadi (A1 dan C2 gacha). "
      + "O'zbekistonda eng ko'p topshiriladigan imtihon.",
    icon: "/jsicons/learn-certificate.png",
    ready: true,
    skills: [
      {
        key: "listening",
        title: "CEFR Listening",
        desc: "6 qism · javob tanlash, qaydnoma, so'zlovchilar, "
          + "xarita, uch parcha va gap to'ldirish.",
        icon: "/jsicons/learn-listening.png",
        href: "/student/ielts/listening?exam=cefr",
        api: "listening",
        hint: "Matnlar Multilevel Master audioskriptidan · har gap "
          + "ikki marta aytiladi",
      },
      {
        key: "reading",
        title: "CEFR Reading",
        desc: "5 qism · matndan so'z topish, e'lonlarga moslash, "
          + "sarlavha, T/F/No Info va A/B/C/D.",
        icon: "/jsicons/learn-reading.png",
        href: "/student/ielts/reading?exam=cefr",
        api: "reading",
        hint: "Beshala qism ham to'liq ishlaydi",
      },
      {
        key: "writing",
        title: "CEFR Writing",
        desc: "Part 1.1 do'stga (B1, 50 so'z) · Part 1.2 rasmiy xat "
          + "(B2, 120-150) · Part 2 blog/forum/maqola (C1, 180-200).",
        icon: "/jsicons/learn-writing.png",
        href: "/student/cefr/writing",
        hint: "Qo'llanma + 186 mashq + 42 vazifa · yozganingiz "
          + "avtomat tekshiriladi",
      },
      {
        key: "speaking",
        title: "CEFR Speaking",
        desc: "3 qism · suhbat, rasm tavsifi va taqqoslash, "
          + "mavzu bo'yicha fikr bildirish.",
        icon: "/jsicons/learn-jony-teacher.png",
      },
    ],
  },
  {
    key: "sat",
    title: "SAT",
    tag: "Digital",
    desc: "AQSH universitetlari uchun · 400-1600 ball · 2 soat 14 "
      + "daqiqa. Kompyuterda, moslashuvchan modullar bilan.",
    icon: "/jsicons/learn-grammar.png",
    ready: false,
    skills: [
      {
        key: "rw",
        title: "Reading and Writing",
        desc: "2 modul · 54 savol · 64 daqiqa. Qisqa matnlar, "
          + "so'z ma'nosi, dalil, grammatika va tinish belgilari.",
        icon: "/jsicons/learn-reading.png",
      },
      {
        key: "math",
        title: "Math",
        desc: "2 modul · 44 savol · 70 daqiqa. Algebra, ma'lumot "
          + "tahlili, murakkab tenglamalar va geometriya.",
        icon: "/jsicons/learn-quiz.png",
      },
    ],
  },
];

export function findExam(key: string | undefined): ExamDef | undefined {
  return EXAMS.find((e) => e.key === key);
}
