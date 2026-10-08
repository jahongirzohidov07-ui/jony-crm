"""NOMZOD BILAN SUHBAT VARAQASI (2026-10-08).

Jahongir HR suhbat savollarini yubordi: "kuchli 10 yillik HR sifatida
tahlil qil, mukammal qil ... nomzodlar degan joyiga qo'shib ber, savol
va javobini yozishga bo'sh joy qoldirib". Asl ro'yxatdan farqi:

  * Raqamlash tuzatildi (9, 10, 13-16 ikki marta, 25/27/33 yo'q edi),
    bir-birini takrorlagan savollar birlashtirildi (xato va
    muvaffaqiyatsizlik, xafa qiladi va bezor qiladi, oylik va ehtiyoj).
  * Farzand yoki oila rejasi haqidagi savol OLIB TASHLANDI: Mehnat
    kodeksi oilaviy holat bo'yicha kamsitishni taqiqlaydi. O'rniga
    hammaga bir xil beriladigan "keyingi 1-2 yildagi rejalar" savoli.
  * "Birinchi oyligingizni bizga berasiz" taklifi OLIB TASHLANDI. Bu
    manipulyatsiya bo'lib, kompaniya obro'siga zarar beradi. O'rniga
    o'qitish va sinov muddati shartlari halol aytiladi.
  * Tashqi ko'rinish "chiroy" emas, ozodalik va kiyinishning mosligi
    bo'yicha baholanadi.
  * Har savolga: maqsad, nimaga e'tibor berish, yaxshi va yomon javob
    belgisi, 1-5 ball. Shunda nomzodlarni bir-biri bilan solishtirsa
    bo'ladi.
  * Rozilik bilan tavsiya (referens) so'rash, norozi ota-ona bilan
    ishlash vaziyati va "bilasizmi?" o'rniga amaliy mini-sinov
    qo'shildi.
  * Savollar "asosiy" (45-60 daqiqa) va "qo'shimcha" ga ajratildi.

Savollar faqat SHU faylda turadi. Ilova, chop etiladigan blank va
hujjat hammasi shu ro'yxatdan chiqadi, shuning uchun bir-biridan
farqlanmaydi.
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import json
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

import models
import roles
from auth import require_role
from database import get_db

router = APIRouter()

GUIDE_VERSION = "2026-10-08"

# kind: "score" — javob + 1-5 ball; "check" — kuzatuv (ha/yo'q);
#       "note"  — faqat javob matni (ball qo'yilmaydi)
# core: True — asosiy savol (vaqt kam bo'lsa ham beriladi)
# only: shu lavozimlar uchun (bo'lmasa — hamma uchun)


def Q(id, text, why="", look="", good="", bad="", kind="score",
      core=False, only=None):
    return {"id": id, "text": text, "why": why, "look": look,
            "good": good, "bad": bad, "kind": kind, "core": core,
            "only": only}


GUIDE = [
    {
        "key": "observe",
        "title": "Suhbatdan oldin: kuzatuv",
        "hint": ("Nomzod buni sezmasligi kerak. Bular faqat qo'shimcha "
                 "belgi, bitta kuzatuvga qarab qaror qilinmaydi."),
        "items": [
            Q("o1", "Vaqtida keldimi? Kechiksa, oldindan xabar berdimi?",
              good="Vaqtida yoki 5-10 daqiqa oldin keldi; kechikadigan "
                   "bo'lsa qo'ng'iroq qildi",
              bad="Kechikdi va uzr ham so'ramadi",
              kind="check", core=True),
            Q("o2", "Kutish joyida o'zini qanday tutdi?",
              look="Jim o'tirdimi, yonidagilar yoki administrator bilan "
                   "gaplashdimi? Keyin 'jamoaga moslashish' savolidagi "
                   "javobi bilan solishtiring.",
              good="Salom berdi, atrofdagilar bilan muloyim gaplashdi",
              bad="Salomsiz kirdi, telefonga ko'milib o'tirdi, "
                  "atrofga befarq",
              kind="check", core=True),
            Q("o3", "Stulga qoldirilgan buyum (telefon, ruchka yoki "
                    "stiker): e'tibor berdimi?",
              good="'Bu kimnikidir' deb eslatdi yoki ehtiyotlab chetga "
                   "qo'ydi",
              bad="Indamay o'tirdi, hatto ustiga o'tirib ketdi",
              kind="check"),
            Q("o4", "Ataylab ochiq qoldirilgan eshik: kirganda yopdimi?",
              good="Orqasidan eshikni ohista yopdi",
              bad="Ochiq qoldirib o'tib ketdi, muhitga befarq",
              kind="check"),
            Q("o5", "Ozodaligi va kiyinishi ish muhitiga mosmi?",
              look="Chiroyi emas: ozodalik, tartib va vaziyatga mos "
                   "kiyinish baholanadi.",
              good="Ozoda, tartibli, ish muhitiga mos",
              bad="Beparvo, ozodaligiga e'tibor bermagan",
              core=True),
        ],
    },
    {
        "key": "intro",
        "title": "1. Tanishuv va motivatsiya",
        "hint": ("Nomzod kirishib olishi uchun boshlang'ich savollar. Bu "
                 "qismda muomala madaniyati va fikrini qanday "
                 "tushuntirishiga e'tibor bering."),
        "items": [
            Q("q1", "O'zingiz haqingizda 2-3 daqiqada gapirib bering.",
              why="Kirishib olish; fikrni tartib bilan tuza olishi",
              good="Qisqa va tartibli: kim, nima qilgan, nimaga intiladi",
              bad="Tarjimai holini boshidan 10 daqiqa gapiradi yoki "
                  "2 gapda to'xtab qoladi",
              core=True),
            Q("q2", "Bu vakansiya haqida qayerdan eshitdingiz?",
              why="Qaysi e'lon kanali yaxshi ishlayotganini bilish",
              look="Javobni kartadagi 'Manba' maydoniga ham belgilang.",
              kind="note"),
            Q("q3", "Jony Academy haqida nimalarni bilasiz? Nega aynan "
                    "bizda ishlamoqchisiz?",
              why="Suhbatga tayyorlanib kelganmi, o'zini 'sota' oladimi",
              good="Sahifamizni ko'rgan, kurs va filiallarni biladi, o'z "
                   "sababini aytadi",
              bad="'Bilmayman, e'lonni ko'rib keldim'; 'uyimga yaqin "
                  "ekan'",
              core=True),
            Q("q4", "Nega aynan shu lavozim?",
              why="Maqsadi faqat ish yoki oylikmi, yo aynan shu ishni "
                  "xohlaydimi",
              good="Ishning mazmunini biladi va uni o'z qiziqishi bilan "
                   "bog'laydi",
              bad="'Qaysi ish bo'lsa ham mayli'",
              core=True),
            Q("q5", "Nega biz aynan sizni tanlashimiz kerak? Boshqalardan "
                    "nimangiz bilan ajralib turasiz?",
              why="Bizga qanday qiymat berishini va o'zini qanchalik "
                  "bilishini aniqlash",
              good="Faktga tayanadi: 'men doim ..., shuning uchun meni "
                   "... deyishadi'; javobi ishga aloqador",
              bad="'Bilmayman, men oddiyman'; 'mas'uliyatliman, harakat "
                  "qilaman' kabi umumiy so'zlar",
              core=True),
        ],
    },
    {
        "key": "experience",
        "title": "2. Tajriba va natijalar",
        "hint": ("Har javobdan keyin aniqlashtiring: 'Aniq misol? Qachon? "
                 "Raqamda qancha? O'zingiz nima qildingiz?' (STAR: "
                 "vaziyat, vazifa, harakat, natija). Haqiqatan ishlagan "
                 "odam ishining detallarini biladi."),
        "items": [
            Q("q6", "Oldin qayerlarda ishlagansiz? Har biridan nega "
                    "ketgansiz?",
              why="Tajribani va ketish sabablarini bilish: bir sabab "
                  "takrorlanyaptimi?",
              good="Har bir joyni va ketish sababini aniq aytadi, sobiq "
                   "rahbarini yomonlamaydi",
              bad="Hamma joydan 'rahbar yomon edi' deb ketgan; 3 oyga "
                  "yetmay tez-tez ish almashtirgan; sababini aytmaydi",
              core=True),
            Q("q7", "Oldingi ish joylaringizdan siz haqingizda fikr "
                    "so'rasak, rozimisiz? Kimga murojaat qilsak bo'ladi?",
              why="Tavsiya (referens) olish uchun nomzodning roziligi va "
                  "aloqa ma'lumoti",
              look="Rozilikni shu yerda oling, ism va telefonni yozib "
                   "qo'ying.",
              good="Ikkilanmay rozi bo'ladi, ism va telefon beradi",
              bad="Bahona qiladi, hech kimni ko'rsatmaydi",
              core=True),
            Q("q8", "Oxirgi ish joyingizda aniq qanday natija "
                    "ko'rsatgansiz? Raqamlarda ayting.",
              why="Natijaga yo'naltirilganmi, raqamlarda fikrlay oladimi",
              look="Umumiy javob bersa: 'Aniq raqam bormidi? Natijani "
                   "qanday o'lchardingiz?' deb so'rang.",
              good="'Oyiga 40 ta qo'ng'iroq qilardim, sotuv 25% dan 35% "
                   "ga chiqdi' kabi aniq raqam",
              bad="'Yaxshi ishladik, mijoz ko'p edi'. Qayta so'ralganda "
                  "ham raqam aytolmaydi",
              core=True),
            Q("q9", "Ishda yoki hayotda erishgan eng katta yutug'ingiz "
                    "nima?",
              why="O'z harakati bilan biror narsaga erishganmi",
              look="Birinchi ishini izlayotgan yoshlardan o'qish, "
                   "ko'ngillilik yoki tanlovlardagi yutuqlarini so'rang.",
              good="O'z kuchi bilan erishgan konkret yutuq",
              bad="Yutug'i yo'q yoki faqat boshqalarning xizmatini "
                  "aytadi"),
            Q("q10", "Bizda birinchi 3 oyda qanday natija ko'rsata olaman "
                     "deb o'ylaysiz? Raqamlarda ayting.",
              why="Dadilligi va raqamlarda reja tuza olishi",
              good="Real va o'lchab bo'ladigan maqsad aytadi",
              bad="'Bor kuchim bilan harakat qilaman'. Shunda 'Bor "
                  "kuchingiz qancha, raqamda?' deb so'rang",
              core=True),
            Q("q11", "Rahbaringiz yoki hamkasbingiz sizni oxirgi marta "
                     "nima uchun maqtagan? Odamlar sizga ko'pincha qanday "
                     "ishni topshiradi?",
              why="Kuchli tomonlarini boshqalar ko'zi bilan bilish",
              good="Aniq voqea va ishni aytadi",
              bad="Eslay olmaydi yoki umumiy gapiradi"),
            Q("q12", "Sizni yaxshi taniydigan 3 kishidan so'rasak, ular "
                     "siz haqingizda nima deyishadi?",
              why="O'zini qanchalik bilishi va kuchli tomonlari",
              good="Har biri uchun aniq sifat va misol aytadi",
              bad="'Bilmayman' yoki faqat maqtov so'zlari"),
        ],
    },
    {
        "key": "growth",
        "title": "3. Xatolar va o'sish",
        "hint": ("Xatosini tan oladigan va undan xulosa chiqaradigan "
                 "odam o'sadi. 'Xato qilmaganman' degan javob — xavfli "
                 "belgi."),
        "items": [
            Q("q13", "Ishda qilgan xatoyingiz yoki muvaffaqiyatsizlikka "
                     "uchragan vaziyatingiz haqida gapirib bering. Keyin "
                     "nima qildingiz?",
              why="Xatoga munosabati: tan oladimi, tuzatadimi, xulosa "
                  "chiqaradimi",
              look="Javob bermasa yumshatib so'rang: 'Masalan, "
                   "rejalashtirgan ishingiz kutilganidek chiqmagan holat? "
                   "Kichik xato bo'lsa ham bo'ladi.'",
              good="Xatoni tan oladi, aybni boshqaga ag'darmaydi, qanday "
                   "tuzatganini va nima o'rganganini aytadi. Bunday "
                   "nomzodga 5 ball qo'ying",
              bad="'Xato qilmaganman', 'Men doim ishga jiddiy "
                  "qaraganman': o'zini ideal ko'rsatishga urinadi",
              core=True),
            Q("q14", "Zaif tomonlaringiz nima? Ular ustida qanday "
                     "ishlayapsiz?",
              why="O'zini tanishi va o'z ustida ishlashi",
              good="Haqiqiy zaif tomonini aytadi va ustida qanday "
                   "ishlayotganini misol bilan ko'rsatadi",
              bad="'Zaif tomonim yo'q'; 'Tez jahlim chiqadi'; 'Ko'p "
                  "gapiradigan odamga toqat qilolmayman' (bunday odam "
                  "mijoz bilan ishlashga mos emas)",
              core=True),
            Q("q15", "Hayotingizda burilish yasagan voqea yoki qiyinchilik "
                     "haqida aytib bering.",
              why="Qiyinchilik ko'rganmi, undan saboq olganmi, rost "
                  "gapiradimi",
              good="Saboq olgan, o'zini tahlil qiladi, bezamasdan rost "
                   "gapiradi",
              bad="'Unday voqea bo'lmagan, hayotim oddiy o'tgan' yoki "
                  "haddan tashqari bezab gapiradi"),
        ],
    },
    {
        "key": "team",
        "title": "4. Jamoa va muloqot",
        "hint": ("Odamlar bilan tez chiqisha oladimi, nizoni qanday hal "
                 "qiladi va jamoaga qanday kayfiyat olib kiradi."),
        "items": [
            Q("q16", "Ishda bo'lgan nizo yoki qiyin vaziyat haqida va uni "
                     "qanday hal qilganingiz haqida gapirib bering.",
              why="Nizoni hal qila olishi; o'z hissasini ko'ra olishi",
              look="Detalini aytmasa: 'Kim bilan? Nima dedingiz? Oxiri "
                   "nima bo'ldi?'",
              good="Vaziyatni batafsil aytadi, o'z xatosini ham ko'radi, "
                   "qanday hal qilganini tushuntiradi",
              bad="'Hech qachon nizo bo'lmagan' yoki faqat boshqalarni "
                  "ayblaydi",
              core=True),
            Q("q17", "Yangi jamoaga qanday moslashasiz? Oxirgi ish "
                     "joyingizda kim bilan tez chiqishib ketgansiz, nega?",
              why="Tashabbus ko'rsatadimi yoki kutib turadimi; kimga "
                  "yaqinlashadi (rahbar, tengdosh, kattalar)",
              good="O'zi boshlaydi: salomlashadi, suhbat qiladi, yordam "
                   "taklif qiladi",
              bad="'Men o'zim bilan bo'laman, sekin moslashaman'"),
            Q("q18", "Sizni ishda nima xafa qiladi yoki bezor qiladi?",
              why="Kayfiyati va stressga munosabati: jamoaga pozitiv "
                  "kayfiyat olib kiradimi",
              good="O'ylab, odob bilan javob beradi: 'Tartibsizlik biroz "
                   "qiynaydi, lekin uni hal qilsa bo'ladi'",
              bad="Ko'p odamni, ishni yoki oldingi ofisni yomonlaydi; "
                  "'Meni turtmasa bo'ldi, aks holda...'",
              core=True),
            Q("q19", "Siz rahbarsiz. Bir xodim doim ishga kechikyapti. "
                     "Nima qilasiz?",
              why="Sabab va oqibatni ko'rib fikrlay oladimi",
              good="Avval yolg'iz suhbatlashib sababini aniqlaydi, keyin "
                   "kelishadi va nazorat qiladi. Sababni aniqlashga "
                   "qaratilgan har qanday javob to'g'ri",
              bad="'Darrov jarima solaman yoki ishdan bo'shataman' — "
                  "sababini so'ramaydi"),
        ],
    },
    {
        "key": "stress",
        "title": "5. Bosim va stressga chidamlilik",
        "hint": ("Real bosim ostida ichki muvozanatini saqlay oladimi. "
                 "Stress-savolni ehtiyotkorlik bilan bering."),
        "items": [
            Q("q20", "Ish paytida bir vaqtda 3 kishi sizga murojaat qilsa, "
                     "qanday yo'l tutasiz?",
              why="Bosim ostida ustuvorlikni belgilay olishi",
              good="Eng tez hal bo'ladiganidan boshlaydi, qolganlarga "
                   "navbatini muloyim aytadi",
              bad="'Bilmayman, har kim navbat bilan gapirsin deyman' — "
                  "bosimdan qochadi",
              core=True),
            Q("q21", "Norozi ota-ona (yoki mijoz) baland ovozda shikoyat "
                     "qilib keldi. Qadamma-qadam nima qilasiz?",
              why="Ta'lim markazida eng ko'p uchraydigan bosimli vaziyat",
              look="Javobidan keyin so'rang: 'Nizoli vaziyatda "
                   "gaplashishning bosqichli texnikasini yoki skript "
                   "bilan ishlashni bilasizmi?'",
              good="Tinglaydi, hamdardlik bildiradi, vaziyatni "
                   "aniqlashtiradi, yechim taklif qiladi, keyin natijani "
                   "tekshiradi",
              bad="Bahslashadi, aybni boshqaga ag'daradi yoki 'rahbarga "
                  "boring' deb qo'ya qoladi",
              core=True),
            Q("q22", "Shubhali ohangda ayting: \"Menimcha, sizda o'zingizga "
                     "ishonch yetishmayotgandek...\"",
              why="Tanqid va bosimga qanday javob berishi",
              look="Faqat bir marta, sokin ohangda ayting. Suhbat oxirida "
                   "bu sinov bo'lganini aytib qo'ying, nomzodda yomon "
                   "taassurot qolmasin.",
              good="Sokin qoladi, muloyim izohlaydi, o'zini himoya "
                   "qilishga o'tmaydi",
              bad="Nigohini olib qochadi, harakatlari tezlashadi: "
                  "'Men unaqa emasman, siz noto'g'ri tushunyapsiz!'"),
            Q("q23", "Ish joyingizga kirdingiz va hamma birdan jim bo'lib "
                     "qoldi. Nima deysiz?",
              why="Hozirjavobligi: noqulay vaziyatdan hazil bilan chiqib "
                  "keta oladimi",
              good="Yengil hazil yoki tabiiy savol bilan vaziyatni "
                   "yumshatadi",
              bad="Qotib qoladi yoki tajovuzkor javob beradi"),
        ],
    },
    {
        "key": "skills",
        "title": "6. Fikrlash, ijodkorlik va amaliy ko'nikma",
        "hint": ("'Bilasizmi?' deb so'ragandan ko'ra ko'rsatib berishini "
                 "so'rang. Bitta mashqqa qarab qaror qilinmaydi."),
        "items": [
            Q("q24", "10 soniyada shu 3 so'zdan bitta gap tuzing: "
                     "muzqaymoq, zamin, hayol.",
              why="Tez fikrlash va hozirjavoblik",
              good="Vaqtida, mazmunli va qiziq gap tuzadi",
              bad="Gap tuza olmaydi yoki uzoq o'ylanib qoladi"),
            Q("q25", "3 daqiqa ichida skripka bilan nimalar qilish "
                     "mumkinligini ayting.",
              why="Ijodkorlik",
              look="Nechta g'oya aytganini sanang va javobga yozing. 4 "
                   "tadan ko'p bo'lsa yaxshi. G'oyalar qanchalik har xil "
                   "ekaniga ham qarang.",
              good="4 tadan ko'p va har xil g'oya",
              bad="1-2 ta g'oya, hammasi 'chalish' atrofida"),
            Q("q26", "Bir chashka shirin choy damlashni boshidan oxirigacha "
                     "ketma-ket tushuntirib bering.",
              why="Tushuntirish qobiliyati: ota-ona va o'quvchiga "
                  "tushuntirish uchun kerak",
              good="Qadamlarni to'liq va tartib bilan aytadi, tinglovchi "
                   "hech narsani bilmaydi deb tushuntiradi",
              bad="Qadamlarni tashlab ketadi, chalkashtiradi",
              core=True),
            Q("q27", "Menga shu ruchkani soting.",
              why="Sotuv ko'nikmasi",
              look="Keyin so'rang: 'Ehtiyoj orqali sotish va "
                   "dekompozitsiya qilib sotish nimaligini bilasizmi?' "
                   "Bilmasa, o'rganishga tayyorligiga qarang.",
              good="Avval ehtiyojni so'raydi (nima uchun kerak, qachon "
                   "yozasiz), keyin foydasini aytadi",
              bad="Faqat ruchkani maqtaydi: 'zo'r ruchka, oling'",
              only="Sotuv, administrator"),
            Q("q28", "Rol o'yini: o'quvchining ota-onasiga sinov darsiga "
                     "yozilish uchun qo'ng'iroq qiling (siz ota-ona "
                     "bo'lasiz).",
              why="Telefonda gaplashish va skript bilan ishlash",
              good="O'zini tanishtiradi, savol beradi, e'tirozga javob "
                   "beradi, aniq kelishuv bilan tugatadi",
              bad="Yodlangan matnni o'qiydi, birinchi e'tirozdayoq "
                  "to'xtaydi",
              only="Sotuv, administrator"),
            Q("q29", "Amaliy mini-sinov: Excel yoki Google Sheets'da "
                     "kichik jadval tuzing (masalan, 5 o'quvchi to'lovi va "
                     "jami summa).",
              why="Hisobot qila oladimi: 3-5 daqiqada ko'rsatib bersin",
              good="Jadvalni o'zi tuzadi, SUM, saralash va filtrni "
                   "ishlata oladi",
              bad="Jadvalni ocholmaydi yoki 'bilaman' deydi-yu, "
                  "qilolmaydi",
              only="Administrator, ofis xodimi"),
        ],
    },
    {
        "key": "values",
        "title": "7. Qadriyatlar va uzoq muddatli reja",
        "hint": ("Bizda qancha muddat ishlashi, nimadan kuch olishi va "
                 "kompaniya qadriyatlariga mosligi."),
        "items": [
            Q("q30", "Sizga nima motivatsiya beradi?",
              why="Ichki (o'sish, o'zini isbotlash) yoki tashqi (pul) "
                  "motivatsiya; qanchalik uzoqqa yetadi",
              look="Ikkalasi ham normal. Muhimi, motivatsiyasi uzoq "
                   "muddatli bo'lsin va o'zi harakat qilsin.",
              good="Aniq, uzoq muddatli manba; o'zi harakat qiladi",
              bad="'Bilmayman' yoki faqat birov itarganda ishlaydi",
              core=True),
            Q("q31", "Hayotingizda ish nechanchi o'rinda turadi? Keyingi "
                     "1-2 yilda ishingizga ta'sir qilishi mumkin bo'lgan "
                     "rejalaringiz bormi (o'qish, ko'chib ketish, boshqa "
                     "ish)?",
              why="Barqarorlik: bizda qancha muddat ishlaydi",
              look="Bu savolni HAMMA nomzodga bir xil bering. Oila "
                   "qurish, homiladorlik yoki farzand rejasini SO'RAMANG: "
                   "Mehnat kodeksiga ko'ra bu kamsitish hisoblanadi.",
              good="Ishga jiddiy qaraydi, o'sishni xohlaydi, rejalarini "
                   "ochiq aytadi",
              bad="'Hozircha bo'sh yurganim uchun keldim, keyin o'qishga "
                  "kiraman'",
              core=True),
            Q("q32", "5 yildan keyin o'zingizni qayerda ko'rasiz?",
              why="Kelajakda ham bizda bo'ladimi",
              good="Rejasi bizdagi o'sish yo'li bilan bog'langan",
              bad="Rejasi yo'q yoki butunlay boshqa sohani ko'zlaydi"),
            Q("q33", "Ishdan tashqari nima bilan shug'ullanasiz? Ijtimoiy "
                     "tarmoqlarda kimlarni doimiy kuzatib borasiz?",
              why="Qiziqishlari qanchalik sog'lom; o'rganishga intiladimi",
              good="Sog'lom qiziqishlar, o'rganishga oid sahifalar "
                   "(kitob, kurs, kasbiy bloglar). Ishga bilvosita foyda "
                   "beradigan qiziqish bo'lsa juda yaxshi",
              bad="Faqat ko'ngilochar sahifalar; 'Instagramda nima "
                  "chiqsa shuni ko'raman'; qiziqishlari juda kam"),
            Q("q34", "Yangi lavozimdan nimalarni kutyapsiz?",
              why="Uning kutganlari biz bera oladigan narsaga mosmi",
              kind="note"),
        ],
    },
    {
        "key": "terms",
        "title": "8. Shartlar",
        "hint": "Raqam va sanalarni aniq yozing — taklif shu asosda tuziladi.",
        "items": [
            Q("q35", "Hozirgi (oxirgi) ishingizda qancha oylik olgansiz? "
                     "Siz uchun minimal, normal va ideal oylik qancha?",
              why="Kutayotgan oyligi bizning imkoniyatimizga mosmi",
              look="Javobni kartadagi 'Kutilayotgan oylik' maydoniga ham "
                   "yozing.",
              kind="note", core=True),
            Q("q36", "Qachondan ish boshlay olasiz (eng erta va eng kech "
                     "sana)? Ish grafigimiz (shanba, kechki soatlar) sizga "
                     "to'g'ri keladimi?",
              kind="note", core=True),
            Q("q37", "Bizda ishga kirgandan keyin o'qitish va sinov muddati "
                     "bor (muddati va shartlarini ayting). Bunga "
                     "tayyormisiz?",
              why="Nima kutilayotganini boshidanoq ochiq kelishib olish",
              look="Shartlarni halol ayting. Nomzoddan o'qitish uchun pul "
                   "yoki oyligini so'ramang.",
              good="Savollar beradi, o'rganishga tayyor",
              bad="O'rganishni xohlamaydi: 'hammasini bilaman'",
              core=True),
        ],
    },
    {
        "key": "close",
        "title": "9. Yakun",
        "hint": "",
        "items": [
            Q("q38", "Men sizdan yana nimani so'ramadim?",
              why="O'zi haqida qo'shimcha aytmoqchi bo'lgan gapi",
              kind="note"),
            Q("q39", "Bizga savollaringiz bormi?",
              why="Ishga qiziqishi",
              good="Ish mazmuni, jamoa va o'sish haqida o'ylangan "
                   "savollar beradi",
              bad="Savoli yo'q yoki faqat 'oylik qachon beriladi?' deb "
                  "so'raydi",
              core=True),
            Q("q40", "Bugungi suhbatdan qanday taassurot oldingiz?",
              why="Ichki hissiyoti va stressga chidamliligi",
              good="'Yaxshi taassurot qoldi, o'zimni sinovda sezdim, bu "
                   "qiziq bo'ldi'",
              bad="'Noqulay bo'ldi, savol juda ko'p, mendan nima "
                  "kutyapsizlar o'zi?'"),
        ],
    },
]

QUESTIONS = {q["id"]: q for sec in GUIDE for q in sec["items"]}


def _recommendations():
    return [{"key": k, "label": l, "tone": t}
            for k, l, t, _v in roles.RECOMMENDATIONS]


def guide_payload() -> dict:
    return {
        "version": GUIDE_VERSION,
        "sections": GUIDE,
        "recommendations": _recommendations(),
        "total": len(QUESTIONS),
        "core_total": sum(1 for q in QUESTIONS.values() if q["core"]),
    }


def _clean_answers(raw) -> dict:
    """Faqat ma'lum savollar, ball 1-5, kuzatuv ha/yo'q. Bo'sh qiymatlar
    tashlab yuboriladi — varaqa ixcham qoladi."""
    out = {}
    for qid, v in (raw or {}).items():
        q = QUESTIONS.get(qid)
        if not q or not isinstance(v, dict):
            continue
        item = {}
        a = (v.get("a") or "").strip() if isinstance(v.get("a"), str) else ""
        if a:
            item["a"] = a[:5000]
        if q["kind"] == "score" and v.get("s") not in (None, ""):
            try:
                s = int(v.get("s"))
            except (TypeError, ValueError):
                raise HTTPException(400, f"{qid}: ball butun son bo'lsin")
            if not 1 <= s <= 5:
                raise HTTPException(400, "Ball 1 dan 5 gacha bo'ladi")
            item["s"] = s
        if q["kind"] == "check" and isinstance(v.get("ok"), bool):
            item["ok"] = v["ok"]
        if item:
            out[qid] = item
    return out


def sheet_stats(answers: dict) -> dict:
    """Foiz = 1-5 ballar o'rtachasi (5 = 100%). Kuzatuvlar foizga
    kirmaydi — ular faqat qo'shimcha belgi."""
    scores = [v["s"] for v in answers.values() if "s" in v]
    checks = [v["ok"] for v in answers.values() if "ok" in v]
    by_section = []
    for sec in GUIDE:
        ss = [answers[q["id"]]["s"] for q in sec["items"]
              if "s" in answers.get(q["id"], {})]
        by_section.append({
            "key": sec["key"], "title": sec["title"],
            "avg": round(sum(ss) / len(ss), 1) if ss else None,
            "count": len(ss),
        })
    return {
        "percent": (round(sum(scores) / len(scores) / 5 * 100, 1)
                    if scores else None),
        "answered": sum(1 for v in answers.values()
                        if v.get("a") or "s" in v or "ok" in v),
        "checks_ok": sum(1 for c in checks if c),
        "checks_total": len(checks),
        "by_section": by_section,
    }


def _sheet_out(db: Session, s: models.InterviewSheet) -> dict:
    try:
        answers = json.loads(s.answers or "{}")
    except ValueError:
        answers = {}
    author = db.query(models.User).get(s.author_id) if s.author_id else None
    rec = {k: (l, t) for k, l, t, _v in roles.RECOMMENDATIONS}
    lbl, tone = rec.get(s.recommendation, (None, None))
    return {
        "id": s.id,
        "author_id": s.author_id,
        "author": author.full_name if author else None,
        "answers": answers,
        "recommendation": s.recommendation,
        "recommendation_label": lbl,
        "recommendation_tone": tone,
        "strengths": s.strengths,
        "concerns": s.concerns,
        "note": s.note,
        **sheet_stats(answers),
        "updated_at": s.updated_at.isoformat() if s.updated_at else None,
    }


def _candidate(db: Session, cid: int, user) -> models.Candidate:
    c = db.query(models.Candidate).get(cid)
    if not c:
        raise HTTPException(404, "Nomzod topilmadi")
    # O'quv bo'limi rahbariga faqat ustoz nomzodlari (hr_ats dagi qoida)
    if user.role == roles.ACADEMIC_HEAD:
        pos = (getattr(c, "position", None) or "").lower()
        if pos != "teacher" and not getattr(c, "subject", None):
            raise HTTPException(
                403, "Bu nomzod ustoz emas — sizga faqat ustoz "
                     "nomzodlari ko'rinadi.")
    return c


def _sync_interview_score(db: Session, c: models.Candidate):
    """Kartadagi 'Intervyu bahosi' (0-10) — barcha varaqalar o'rtachasi.
    Varaqada ball bo'lmasa, qo'lda yozilgan qiymatga tegilmaydi."""
    vals = [s.percent for s in db.query(models.InterviewSheet).filter(
        models.InterviewSheet.candidate_id == c.id).all()
        if s.percent is not None]
    if vals:
        c.interview_score = round(sum(vals) / len(vals) / 10, 1)


@router.get("/api/hr/interview-guide")
def interview_guide(user=Depends(require_role(*roles.HR_CANDIDATE_VIEW))):
    """Bo'sh savollar ro'yxati — chop etish uchun ham."""
    return guide_payload()


@router.get("/api/candidates/{cid}/interview-sheet")
def interview_sheet_get(cid: int, db: Session = Depends(get_db),
                        user=Depends(require_role(
                            *roles.HR_CANDIDATE_VIEW))):
    c = _candidate(db, cid, user)
    sheets = [_sheet_out(db, s) for s in db.query(models.InterviewSheet)
              .filter(models.InterviewSheet.candidate_id == cid)
              .order_by(models.InterviewSheet.updated_at.desc()).all()]
    return {
        "candidate": {"id": c.id, "full_name": c.full_name,
                      "phone": c.phone,
                      "position": getattr(c, "position", None),
                      "subject": getattr(c, "subject", None)},
        "guide": guide_payload(),
        "mine": next((s for s in sheets if s["author_id"] == user.id),
                     None),
        "others": [s for s in sheets if s["author_id"] != user.id],
    }


class SheetIn(BaseModel):
    answers: dict = {}
    recommendation: Optional[str] = None
    strengths: Optional[str] = None
    concerns: Optional[str] = None
    note: Optional[str] = None


@router.put("/api/candidates/{cid}/interview-sheet")
def interview_sheet_save(cid: int, payload: SheetIn,
                         db: Session = Depends(get_db),
                         user=Depends(require_role(
                             *roles.HR_CANDIDATE_VIEW))):
    """O'z varaqasini saqlaydi (avto-saqlash ham shu yerga keladi).
    Boshqa suhbatdoshning varaqasini o'zgartirib bo'lmaydi."""
    c = _candidate(db, cid, user)
    if payload.recommendation and payload.recommendation not in \
            roles.RECOMMENDATION_LABELS:
        raise HTTPException(400, "Tavsiya noto'g'ri")
    answers = _clean_answers(payload.answers)
    s = db.query(models.InterviewSheet).filter(
        models.InterviewSheet.candidate_id == cid,
        models.InterviewSheet.author_id == user.id).first()
    if not s:
        s = models.InterviewSheet(candidate_id=cid, author_id=user.id,
                                  created_at=datetime.utcnow())
        db.add(s)
    st = sheet_stats(answers)
    s.answers = json.dumps(answers, ensure_ascii=False)
    s.recommendation = payload.recommendation or None
    s.strengths = (payload.strengths or "").strip() or None
    s.concerns = (payload.concerns or "").strip() or None
    s.note = (payload.note or "").strip() or None
    s.percent = st["percent"]
    s.answered = st["answered"]
    s.guide_version = GUIDE_VERSION
    s.updated_at = datetime.utcnow()
    db.flush()
    _sync_interview_score(db, c)
    db.commit(); db.refresh(s)
    return _sheet_out(db, s)
