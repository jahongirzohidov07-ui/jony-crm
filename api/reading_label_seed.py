# -*- coding: utf-8 -*-
"""IELTS READING — LABELLING A DIAGRAM (2026-08-25).

Jahongir: "bu diagram labelling savol turigan bularni samalyotni
15ga, elektric revolutionni 10tga qoysang qolganini osondan qiyinga
qarab ketaveradigan qilasang."

TUZILISHI. 20 ta chizma, jami 103 yorliq, daraja 1..20:
  1-9    — oddiy narsalar (velosiped, uy, daraxt, fotoapparat) —
           yorliq matndagi jumlaga deyarli aynan mos;
  10     — "READING #10. The electric revolution" (namuna);
  11-14  — oraliq (suv tozalash, quloq, shlyuz, quyosh paneli);
  15     — "READING #11. The Boeing 787" (namuna);
  16-20  — eng qiyini: GES, issiqxona, chuchuklashtirish, reaktiv
           dvigatel, kosmik stansiya.

BU TURNING O'ZIGA XOSLIGI. Chizmada har yorliq QISMGA ishora
qiladi. Shuning uchun birinchi ish — yorliq qaysi qismga
tegishliligini aniqlash, keyin matndan o'sha qism tasvirlangan
jumlani topish. Chizma matn tartibida BORMASLIGI mumkin: rasmda
o'ng tomondagi yorliq matnning boshida yozilgan bo'lishi mumkin.

Javob 2 so'zdan oshmaydi (NO MORE THAN TWO WORDS AND/OR A NUMBER).
"""

SKILL = "ielts_reading"
KIND = "read_label"

# =====================================================================
#  QOIDALAR
# =====================================================================
LABEL_TIPS = [
    ("Labelling a Diagram nima",
     "Chizma beriladi, uning qismlariga yorliq yozilgan, ba'zi "
     "yorliqlarda bo'sh joy bor. Bo'shliqni MATNDAN olingan so'z "
     "bilan to'ldirasiz.",
     "Yorliq: «Battery allows travel of up to ______ in cities»\n"
     "Matn: «the car is capable of as much as 160 km in urban "
     "motoring conditions»\nJavob: 160 km"),
    ("1-QADAM — yorliq QAYSI QISMGA tegishli",
     "Har yorliq chizmaning ma'lum qismiga ishora qiladi. Avval "
     "shu qismni aniqlang (batareya, oyna, dvigatel, tomir), keyin "
     "matndan o'sha qism tasvirlangan jumlani qidiring. Qismni "
     "aniqlamasdan qidirsangiz — boshqa jumlaga tushib qolasiz.",
     ""),
    ("TARTIBGA ISHONMANG",
     "Flow-chart matn tartibida borardi. Chizma ESA YO'Q — rasmda "
     "yuqoridagi yorliq matnning oxirida, pastdagisi boshida "
     "bo'lishi mumkin. Bu yerda faqat QISM nomi yo'l ko'rsatadi.",
     "Boeing 787 chizmasida 1-yorliq («lighter») matnning "
     "1-xatboshida, 3-yorliq («210 passengers») esa 2-xatboshida."),
    ("Paraffraz baribir kerak",
     "Yorliqdagi ibora matnda aynan turmaydi.",
     "Yorliq: «reduces the amount of ______ that the airliner "
     "needs»\nMatn: «uses 20 percent less fuel»\nJavob: fuel\n\n"
     "Yorliq: «Engineers can fit a new engine in a ______»\n"
     "Matn: «the engines can be changed in a much shorter time»"),
    ("So'z TURINI bo'shliq atrofidan aniqlang",
     "«made much ______ than aluminium» — SIFAT (lighter). "
     "«passing an ______ through them» — OT (electric current). "
     "«increased by ______» — SON yoki foiz.", ""),
    ("Ikki so'zgacha",
     "«NO MORE THAN TWO WORDS AND/OR A NUMBER»: «160 km», "
     "«electricity grid», «210 passengers», «electric current». "
     "Uchta so'z yozilsa javob noto'g'ri sanaladi.", ""),
    ("Chalg'ituvchi sonlardan ehtiyot",
     "Texnik matnda son ko'p bo'ladi: 1,500 varaq, 40,000 mahkamlash, "
     "20 foiz, 210 yo'lovchi, 15,200 km, 65 foiz. Yorliq qaysi "
     "qismga tegishli ekaniga qarab tanlang.", ""),
    ("Chizmada bir necha qism bir xil ko'rinadi",
     "«charge point» uyda ham, ishxonada ham, do'konda ham bor. "
     "Yorliqdagi qo'shimcha so'z («through home charge point», "
     "«or shops») qaysi biri kerakligini aytadi.", ""),
]


def P(level, title, text, figure, labels, gaps):
    return {"level": level, "title": title, "text": text,
            "figure": figure, "labels": labels, "gaps": gaps}


PASSAGES = []

# ---------------------------------------------------------------- 1
PASSAGES.append(P(
    1, "PARTS OF A BICYCLE",
    "A bicycle has two wheels held by a metal frame. The rider sits "
    "on the saddle and holds the handlebars to steer. Power comes "
    "from the pedals, which turn a chain connected to the back "
    "wheel. Brakes on both wheels stop the bicycle, and a bell warns "
    "people ahead.",
    "A bicycle",
    ["1. The rider sits on the ___1.",
     "2. The rider steers using the ___2.",
     "3. The ___3 turn the chain.",
     "4. The chain is connected to the ___4 wheel.",
     "5. The ___5 warns people ahead."],
    [(1, "saddle", "The rider sits on the ______",
      "The rider sits on the saddle", "Qism nomi to'g'ridan-to'g'ri."),
     (2, "handlebars", "steers using the ______",
      "holds the handlebars to steer",
      "PARAFFRAZ: steers using = holds ... to steer."),
     (3, "pedals", "The ______ turn the chain",
      "Power comes from the pedals, which turn a chain",
      "Qaysi qism zanjirni aylantiradi."),
     (4, "back", "connected to the ______ wheel",
      "a chain connected to the back wheel", "Qaysi g'ildirak."),
     (5, "bell", "The ______ warns people ahead",
      "a bell warns people ahead", "Ovoz beruvchi qism.")],
))

# ---------------------------------------------------------------- 2
PASSAGES.append(P(
    2, "A SIMPLE HOUSE",
    "The front door opens into a hall. On the left is the kitchen, "
    "where the family cooks and eats. The living room is on the "
    "right and has a large window facing the garden. Two bedrooms "
    "are upstairs, and between them is a small bathroom. Water is "
    "heated by a boiler in the cellar.",
    "A house",
    ["1. The front door opens into the ___1.",
     "2. The family cooks in the ___2.",
     "3. The ___3 has a large window facing the garden.",
     "4. A small ___4 lies between the two bedrooms.",
     "5. The ___5 in the cellar heats the water."],
    [(1, "hall", "opens into the ______",
      "The front door opens into a hall", "Kirish joyi."),
     (2, "kitchen", "The family cooks in the ______",
      "the kitchen, where the family cooks and eats", "Xona nomi."),
     (3, "living room", "______ has a large window",
      "The living room is on the right and has a large window",
      "Ikki so'zli javob."),
     (4, "bathroom", "A small ______ lies between",
      "between them is a small bathroom", "Joylashuv."),
     (5, "boiler", "The ______ in the cellar",
      "Water is heated by a boiler in the cellar", "Uskuna nomi.")],
))

# ---------------------------------------------------------------- 3
PASSAGES.append(P(
    3, "PARTS OF A TREE",
    "The roots hold the tree in the ground and draw up water and "
    "minerals from the soil. The trunk carries this liquid upwards "
    "and gives the tree its height. Bark covers the trunk and "
    "protects it from insects and cold. Branches spread out from the "
    "trunk, and the leaves at their ends use sunlight to make food.",
    "A tree",
    ["1. The ___1 draw up water from the soil.",
     "2. The ___2 carries liquid upwards.",
     "3. ___3 protects the trunk from insects.",
     "4. ___4 spread out from the trunk.",
     "5. The ___5 use sunlight to make food."],
    [(1, "roots", "The ______ draw up water",
      "The roots hold the tree in the ground and draw up water",
      "Pastdagi qism."),
     (2, "trunk", "The ______ carries liquid upwards",
      "The trunk carries this liquid upwards", "O'rta qism."),
     (3, "Bark", "______ protects the trunk",
      "Bark covers the trunk and protects it", "Qoplama."),
     (4, "Branches", "______ spread out from the trunk",
      "Branches spread out from the trunk", "Tarmoqlar."),
     (5, "leaves", "The ______ use sunlight",
      "the leaves at their ends use sunlight to make food",
      "Uchidagi qism.")],
))

# ---------------------------------------------------------------- 4
PASSAGES.append(P(
    4, "A SCHOOL BAG",
    "The main compartment of the bag holds books and folders. In "
    "front of it there is a smaller pocket for pens and a "
    "calculator. A mesh pocket on the side carries a water bottle. "
    "The bag is worn on the back using two padded straps, and a "
    "handle on top allows it to be carried by hand.",
    "A school bag",
    ["1. The main ___1 holds books.",
     "2. A smaller ___2 in front holds pens.",
     "3. A mesh pocket on the side carries a ___3.",
     "4. Two padded ___4 go over the shoulders.",
     "5. A ___5 on top is used to carry it by hand."],
    [(1, "compartment", "The main ______ holds books",
      "The main compartment of the bag holds books", "Asosiy qism."),
     (2, "pocket", "A smaller ______ in front",
      "there is a smaller pocket for pens", "Old qismdagi cho'ntak."),
     (3, "water bottle", "carries a ______",
      "A mesh pocket on the side carries a water bottle",
      "Ikki so'zli javob."),
     (4, "straps", "Two padded ______",
      "worn on the back using two padded straps", "Yelka qismi."),
     (5, "handle", "A ______ on top",
      "a handle on top allows it to be carried by hand",
      "Tepadagi qism.")],
))

# ---------------------------------------------------------------- 5
PASSAGES.append(P(
    5, "A KITCHEN",
    "Against the far wall stands the cooker, with an extractor fan "
    "above it to remove steam. The sink is placed under the window "
    "so that there is light for washing up. Between them runs a long "
    "worktop where food is prepared. The fridge stands in the "
    "corner, and cups and plates are kept in cupboards fixed to the "
    "wall.",
    "A kitchen",
    ["1. An ___1 above the cooker removes steam.",
     "2. The ___2 is under the window.",
     "3. Food is prepared on the ___3.",
     "4. The ___4 stands in the corner.",
     "5. Plates are kept in ___5 fixed to the wall."],
    [(1, "extractor fan", "An ______ above the cooker",
      "with an extractor fan above it to remove steam",
      "Ikki so'zli javob."),
     (2, "sink", "The ______ is under the window",
      "The sink is placed under the window", "Joylashuv bo'yicha."),
     (3, "worktop", "Food is prepared on the ______",
      "a long worktop where food is prepared", "Ish yuzasi."),
     (4, "fridge", "The ______ stands in the corner",
      "The fridge stands in the corner", "Burchakdagi qism."),
     (5, "cupboards", "kept in ______ fixed to the wall",
      "kept in cupboards fixed to the wall", "Devordagi qism.")],
))

# ---------------------------------------------------------------- 6
PASSAGES.append(P(
    6, "A DIGITAL CAMERA",
    "Light enters the camera through the lens, which can be turned "
    "to focus the image. Behind the lens sits the shutter, a curtain "
    "that opens for a fraction of a second. The light then falls on "
    "the sensor, which converts it into an electrical signal. The "
    "picture is stored on a memory card, and the photographer checks "
    "it on the screen at the back.",
    "A digital camera",
    ["1. Light enters through the ___1.",
     "2. The ___2 opens for a fraction of a second.",
     "3. The ___3 turns light into an electrical signal.",
     "4. Pictures are stored on a ___4.",
     "5. The photographer checks the picture on the ___5."],
    [(1, "lens", "Light enters through the ______",
      "Light enters the camera through the lens", "Old qism."),
     (2, "shutter", "The ______ opens for a fraction of a second",
      "the shutter, a curtain that opens for a fraction of a second",
      "Parda vazifasidagi qism."),
     (3, "sensor", "The ______ turns light into an electrical signal",
      "the sensor, which converts it into an electrical signal",
      "PARAFFRAZ: turns into = converts into."),
     (4, "memory card", "stored on a ______",
      "The picture is stored on a memory card", "Ikki so'z."),
     (5, "screen", "checks the picture on the ______",
      "the photographer checks it on the screen at the back",
      "Orqa qism.")],
))

# ---------------------------------------------------------------- 7
PASSAGES.append(P(
    7, "A RIVER SYSTEM",
    "A river begins at its source, often a spring high in the hills. "
    "Small streams called tributaries join it as it flows downhill, "
    "increasing its volume. In the upper course the water cuts "
    "steep-sided valleys, while further down the river slows and "
    "curves into loops known as meanders. Where the river finally "
    "meets the sea it drops its load of sand and mud, sometimes "
    "building a fan-shaped delta.",
    "A river system",
    ["1. The river begins at its ___1.",
     "2. Smaller streams that join it are called ___2.",
     "3. In its upper course the river cuts steep-sided ___3.",
     "4. Lower down the river curves into ___4.",
     "5. At the sea it may build a fan-shaped ___5."],
    [(1, "source", "begins at its ______",
      "A river begins at its source", "Boshlanish nuqtasi."),
     (2, "tributaries", "streams that join it are called ______",
      "Small streams called tributaries join it", "Qo'shiluvchilar."),
     (3, "valleys", "cuts steep-sided ______",
      "the water cuts steep-sided valleys", "Yuqori oqim."),
     (4, "meanders", "curves into ______",
      "the river slows and curves into loops known as meanders",
      "PARAFFRAZ: curves into = curves into loops known as."),
     (5, "delta", "build a fan-shaped ______",
      "sometimes building a fan-shaped delta", "Dengizga quyilish.")],
))

# ---------------------------------------------------------------- 8
PASSAGES.append(P(
    8, "A WIND TURBINE",
    "Three long blades catch the wind and turn slowly, at about "
    "fifteen revolutions a minute. They are attached to a hub, which "
    "drives a shaft inside the nacelle, the box behind the blades. "
    "Because a generator needs far higher speeds, a gearbox raises "
    "the rate to around 1,500 revolutions. The electricity produced "
    "travels down cables inside the tower to a transformer at the "
    "base.",
    "A wind turbine",
    ["1. Three ___1 catch the wind.",
     "2. They are fixed to a ___2.",
     "3. The ___3 is the box behind the blades.",
     "4. A ___4 raises the speed for the generator.",
     "5. Cables run down the tower to a ___5."],
    [(1, "blades", "Three ______ catch the wind",
      "Three long blades catch the wind", "Aylanuvchi qism."),
     (2, "hub", "fixed to a ______",
      "They are attached to a hub",
      "PARAFFRAZ: fixed to = attached to."),
     (3, "nacelle", "The ______ is the box behind the blades",
      "the nacelle, the box behind the blades", "Korpus nomi."),
     (4, "gearbox", "A ______ raises the speed",
      "a gearbox raises the rate to around 1,500 revolutions",
      "PARAFFRAZ: speed = rate. Chalg'ituvchi: 15 va 1,500."),
     (5, "transformer", "down the tower to a ______",
      "travels down cables inside the tower to a transformer",
      "Pastdagi qurilma.")],
))

# ---------------------------------------------------------------- 9
PASSAGES.append(P(
    9, "A VOLCANO",
    "Molten rock collects in a magma chamber several kilometres "
    "below the surface. Pressure forces it upwards through a narrow "
    "pipe called the vent. At the top the vent opens into a crater, "
    "the bowl-shaped hollow from which ash and gas escape. Some "
    "magma pushes sideways through cracks and emerges from a "
    "secondary opening on the flank, known as a side vent. Layers of "
    "cooled lava and ash build the cone.",
    "A volcano",
    ["1. Molten rock gathers in a ___1 below the surface.",
     "2. It rises through a narrow pipe called the ___2.",
     "3. The vent opens into a bowl-shaped ___3.",
     "4. A ___4 lets magma out on the side of the mountain.",
     "5. Layers of lava and ash build the ___5."],
    [(1, "magma chamber", "gathers in a ______",
      "Molten rock collects in a magma chamber",
      "PARAFFRAZ: gathers = collects. Ikki so'z."),
     (2, "vent", "narrow pipe called the ______",
      "upwards through a narrow pipe called the vent", "Kanal."),
     (3, "crater", "opens into a bowl-shaped ______",
      "the vent opens into a crater, the bowl-shaped hollow",
      "Tepadagi chuqurlik."),
     (4, "side vent", "A ______ lets magma out on the side",
      "emerges from a secondary opening on the flank, known as a "
      "side vent", "PARAFFRAZ: on the side = on the flank."),
     (5, "cone", "build the ______",
      "Layers of cooled lava and ash build the cone", "Tog' shakli.")],
))

# --------------------------------------------------------------- 10
#  JAHONGIRNING NAMUNASI — READING #10
PASSAGES.append(P(
    10, "READING #10. THE ELECTRIC REVOLUTION",
    "The main reasons why electric cars are not more popular at "
    "present are their price and their relatively small range. "
    "Existing battery systems only allow electric cars to travel a "
    "distance of between 100 and 160 km. However, this distance may "
    "not be a problem for urban drivers. A recent Sydney study "
    "reported that 20 percent of journeys were 30 km or less, and "
    "recent data from the US suggests that 60 percent of trips taken "
    "there are 48 km or less.\n\n"
    "An innovative company called Better Place is aiming to make "
    "electric cars an option for all drivers. It wants to see "
    "existing vehicles replaced by electric vehicles which, it says, "
    "offer a number of benefits. Firstly, they can be powered by "
    "renewable energy which produces zero emissions. What is more, "
    "electric motors are more efficient and can convert more than 90 "
    "percent of power into movement, whereas the efficiency of "
    "diesel or petrol engines is less than 20 percent. To achieve "
    "its aim, Better Place plans to use technology which is already "
    "available.\n\n"
    "The plan is simple but revolutionary. It starts with the "
    "installation of a home charge point, and through this, the "
    "vehicle will be plugged into the electricity grid whenever it "
    "is in the garage, typically at night. In the morning, with a "
    "fully charged battery, the car is capable of as much as 160 km "
    "in urban motoring conditions. In addition to the home charge "
    "point, the battery can be topped up by charge points at work "
    "and at supermarkets.\n\n"
    "The battery is linked to a control centre by smart technology "
    "inside the vehicle. Better Place can then ensure that the car "
    "is charged with electricity from renewable sources at the "
    "cheapest price. For longer trips, a navigation system directs "
    "the driver to the nearest switch station, where the depleted "
    "battery can be replaced with a charged one by a robot within a "
    "couple of minutes.",
    "An electric car",
    ["1. Car connects to ___1 through home charge point.",
     "2. Battery allows travel of up to ___2 in cities.",
     "3. Battery can be recharged at ___3 or shops.",
     "4. Car communicates with control centre to receive power at "
     "the lowest ___4.",
     "5. ___5 inside car locates switch stations.",
     "6. ___6 at switch centre will change batteries."],
    [(1, "electricity grid", "Car connects to ______",
      "the vehicle will be plugged into the electricity grid",
      "PARAFFRAZ: connects to = will be plugged into. Ikki so'z."),
     (2, "160 km", "travel of up to ______ in cities",
      "the car is capable of as much as 160 km in urban motoring "
      "conditions",
      "PARAFFRAZ: up to = as much as; in cities = urban. "
      "Chalg'ituvchi: 100 km, 30 km, 48 km."),
     (3, "work", "recharged at ______ or shops",
      "the battery can be topped up by charge points at work and "
      "at supermarkets",
      "PARAFFRAZ: shops = supermarkets, demak ikkinchisi «work»."),
     (4, "price", "receive power at the lowest ______",
      "charged with electricity from renewable sources at the "
      "cheapest price",
      "PARAFFRAZ: lowest = cheapest."),
     (5, "navigation system", "______ inside car locates switch "
      "stations",
      "a navigation system directs the driver to the nearest switch "
      "station",
      "PARAFFRAZ: locates = directs the driver to the nearest. "
      "Ikki so'z."),
     (6, "robot", "______ at switch centre will change batteries",
      "the depleted battery can be replaced with a charged one by a "
      "robot", "PARAFFRAZ: change = be replaced.")],
))

# --------------------------------------------------------------- 11
PASSAGES.append(P(
    11, "A WATER TREATMENT WORKS",
    "Raw water arriving from the reservoir first passes through a "
    "screen, a metal grid that removes leaves and larger rubbish. In "
    "the next stage a chemical called a coagulant is added, causing "
    "fine particles to stick together into clumps heavy enough to "
    "settle. The water then flows slowly through a sedimentation "
    "tank, where these clumps fall to the bottom as sludge. What "
    "remains passes downwards through a bed of sand, which traps the "
    "last small particles. Finally chlorine is added to kill "
    "bacteria before the water enters the supply.",
    "A water treatment works",
    ["1. A metal ___1 removes leaves and rubbish.",
     "2. A ___2 makes fine particles stick together.",
     "3. Clumps fall to the bottom of the ___3 as sludge.",
     "4. A bed of ___4 traps the last small particles.",
     "5. ___5 is added to kill bacteria."],
    [(1, "screen", "A metal ______ removes leaves",
      "passes through a screen, a metal grid that removes leaves",
      "Birinchi bosqich."),
     (2, "coagulant", "A ______ makes fine particles stick together",
      "a chemical called a coagulant is added, causing fine "
      "particles to stick together", "Kimyoviy modda nomi."),
     (3, "sedimentation tank", "bottom of the ______",
      "flows slowly through a sedimentation tank, where these "
      "clumps fall to the bottom", "Ikki so'zli javob."),
     (4, "sand", "A bed of ______ traps",
      "passes downwards through a bed of sand, which traps the last "
      "small particles", "Filtr materiali."),
     (5, "Chlorine", "______ is added to kill bacteria",
      "Finally chlorine is added to kill bacteria",
      "Oxirgi bosqich.")],
))

# --------------------------------------------------------------- 12
PASSAGES.append(P(
    12, "THE HUMAN EAR",
    "Sound waves are gathered by the outer ear and travel along a "
    "short tube to the eardrum, a thin membrane which vibrates. "
    "These vibrations are passed on and made stronger by three tiny "
    "bones, the smallest in the body, known together as the "
    "ossicles. The last of them presses against the cochlea, a "
    "spiral chamber filled with fluid and lined with thousands of "
    "hair cells. Movement of the fluid bends these cells, which send "
    "impulses along the auditory nerve to the brain.",
    "The human ear",
    ["1. Sound is gathered by the ___1 ear.",
     "2. The ___2 is a thin membrane that vibrates.",
     "3. Three tiny bones, the ___3, make vibrations stronger.",
     "4. The ___4 is a spiral chamber filled with fluid.",
     "5. Impulses travel to the brain along the ___5."],
    [(1, "outer", "gathered by the ______ ear",
      "Sound waves are gathered by the outer ear", "Tashqi qism."),
     (2, "eardrum", "The ______ is a thin membrane",
      "travel along a short tube to the eardrum, a thin membrane "
      "which vibrates", "Parda."),
     (3, "ossicles", "Three tiny bones, the ______",
      "three tiny bones, the smallest in the body, known together "
      "as the ossicles", "PARAFFRAZ: known together as."),
     (4, "cochlea", "The ______ is a spiral chamber",
      "presses against the cochlea, a spiral chamber filled with "
      "fluid", "Spiral bo'shliq."),
     (5, "auditory nerve", "along the ______",
      "which send impulses along the auditory nerve to the brain",
      "Ikki so'zli javob.")],
))

# --------------------------------------------------------------- 13
PASSAGES.append(P(
    13, "A CANAL LOCK",
    "A lock allows boats to move between stretches of water at "
    "different heights. The boat enters through the lower gates into "
    "an enclosed space called the chamber. These gates are then "
    "closed and small openings, known as paddles, are raised in the "
    "upper gates. Water flows in by gravity alone — no pump is used "
    "— and the boat rises with it. When the levels match, the upper "
    "gates swing open and the boat continues. The whole operation "
    "takes about ten minutes.",
    "A canal lock",
    ["1. The boat enters through the lower ___1.",
     "2. The enclosed space is called the ___2.",
     "3. Openings known as ___3 are raised in the upper gates.",
     "4. Water flows in by ___4, without a pump.",
     "5. The whole operation takes about ___5."],
    [(1, "gates", "enters through the lower ______",
      "The boat enters through the lower gates", "Kirish qismi."),
     (2, "chamber", "enclosed space is called the ______",
      "into an enclosed space called the chamber", "Bo'shliq nomi."),
     (3, "paddles", "Openings known as ______",
      "small openings, known as paddles, are raised in the upper "
      "gates", "Teshiklar nomi."),
     (4, "gravity", "Water flows in by ______",
      "Water flows in by gravity alone — no pump is used",
      "Kuch manbai."),
     (5, "ten minutes", "takes about ______",
      "The whole operation takes about ten minutes",
      "Ikki so'zli javob.")],
))

# --------------------------------------------------------------- 14
PASSAGES.append(P(
    14, "A HOME SOLAR SYSTEM",
    "Panels on the roof contain cells which turn sunlight directly "
    "into direct current. Because household appliances need "
    "alternating current, the electricity passes through an "
    "inverter, usually mounted in the loft or garage. A meter then "
    "records how much power the household uses and how much is sent "
    "back to the grid. Surplus energy may instead be kept in a "
    "battery for use after dark. A small isolator switch allows an "
    "engineer to cut the system off safely for repairs.",
    "A home solar system",
    ["1. ___1 on the roof turn sunlight into direct current.",
     "2. An ___2 changes it to alternating current.",
     "3. A ___3 records how much power is used.",
     "4. Surplus energy can be kept in a ___4.",
     "5. An ___5 lets an engineer cut the system off."],
    [(1, "Panels", "______ on the roof turn sunlight",
      "Panels on the roof contain cells which turn sunlight "
      "directly into direct current", "Tomdagi qism."),
     (2, "inverter", "An ______ changes it to alternating current",
      "the electricity passes through an inverter",
      "PARAFFRAZ: changes = passes through ... to convert."),
     (3, "meter", "A ______ records how much power is used",
      "A meter then records how much power the household uses",
      "Hisoblagich."),
     (4, "battery", "kept in a ______",
      "Surplus energy may instead be kept in a battery",
      "Saqlash qurilmasi."),
     (5, "isolator switch", "An ______ lets an engineer cut the "
      "system off",
      "A small isolator switch allows an engineer to cut the system "
      "off safely", "Ikki so'zli javob.")],
))

# --------------------------------------------------------------- 15
#  JAHONGIRNING NAMUNASI — READING #11
PASSAGES.append(P(
    15, "READING #11. THE BOEING 787",
    "Until now, airliner fuselages have been made of aluminium "
    "sheets. Large aircraft can have 1,500 of these sheets with "
    "between 40,000 and 50,000 metal fasteners. The 787 is the first "
    "airliner to be built with a one-piece fuselage made from a "
    "special material called 'composite'. Not only does this make "
    "the airliner quicker and easier to build, but it also makes it "
    "a lot lighter.\n\n"
    "The advantage of this weight reduction is that the 787 uses 20 "
    "percent less fuel than other airliners of a similar size, which "
    "makes it much more environmentally friendly. The reduced weight "
    "also means that the Boeing 787 can fly further than many other "
    "airliners of a similar size, carrying 210 passengers or more up "
    "to 15,200 kilometres before refuelling.\n\n"
    "Sometimes an airliner needs to change from one type of engine "
    "to another. This is a difficult and time-consuming process. The "
    "787 has a revolutionary engine attachment on the wing which "
    "means that the engines can be changed in a much shorter time. "
    "The case containing the engine is also different from those on "
    "other airliners. It has been designed to cut down the noise "
    "from the engine, making it less noisy for passengers in the "
    "cabin as well as for people on the ground.\n\n"
    "In addition to a quieter cabin, passengers will also benefit "
    "from windows which are 65 percent larger than those on other "
    "airliners, giving them a much better view of the world passing "
    "by below them. The windows also have a unique facility which "
    "allows passengers or cabin crew to control the amount of light "
    "that enters them. This is thanks to a liquid in the window "
    "which reacts to an electric current. When a passenger or cabin "
    "crew member presses a button, the current causes a chemical "
    "reaction in the window which darkens the liquid.",
    "The Boeing 787",
    ["1. Composite fuselage material is much ___1 than traditional "
     "aluminium sheets.",
     "2. Composite fuselage material reduces the amount of ___2 "
     "that the airliner needs.",
     "3. Airliner can accommodate at least ___3.",
     "4. Engineers can fit a new engine in a ___4 than it takes on "
     "other airliners.",
     "5. A special engine case reduces ___5.",
     "6. The size of the windows has increased by ___6.",
     "7. Window glass can be made darker by passing an ___7 through "
     "them."],
    [(1, "lighter", "material is much ______ than aluminium sheets",
      "but it also makes it a lot lighter",
      "PARAFFRAZ: much = a lot. Bo'shliqdan keyin «than» — "
      "TAQQOSLASH shakli kerak."),
     (2, "fuel", "reduces the amount of ______",
      "the 787 uses 20 percent less fuel than other airliners",
      "PARAFFRAZ: reduces the amount of = uses less."),
     (3, "210 passengers", "accommodate at least ______",
      "carrying 210 passengers or more up to 15,200 kilometres",
      "PARAFFRAZ: at least = or more. Chalg'ituvchi: 15,200 km, "
      "1,500 varaq, 40,000 mahkamlagich."),
     (4, "shorter time", "fit a new engine in a ______",
      "which means that the engines can be changed in a much "
      "shorter time",
      "PARAFFRAZ: fit a new engine = engines can be changed. "
      "Ikki so'z."),
     (5, "noise", "engine case reduces ______",
      "It has been designed to cut down the noise from the engine",
      "PARAFFRAZ: reduces = cut down."),
     (6, "65 percent", "windows has increased by ______",
      "windows which are 65 percent larger than those on other "
      "airliners", "PARAFFRAZ: increased by = larger than."),
     (7, "electric current", "passing an ______ through them",
      "thanks to a liquid in the window which reacts to an electric "
      "current", "Ikki so'zli javob.")],
))

# --------------------------------------------------------------- 16
PASSAGES.append(P(
    16, "A HYDROELECTRIC DAM",
    "Water held behind the dam forms a reservoir, and the difference "
    "in level between its surface and the outlet is called the head "
    "— the greater the head, the more energy is available. Water is "
    "drawn from an intake set well below the surface and travels "
    "down a steep pipe known as the penstock. At the bottom it "
    "strikes the curved buckets of a turbine, spinning it at "
    "constant speed. A shaft carries this rotation to the generator "
    "above. Spent water leaves through a wide channel called the "
    "tailrace and rejoins the river downstream.",
    "A hydroelectric dam",
    ["1. Water stored behind the dam forms a ___1.",
     "2. The difference in level is called the ___2.",
     "3. Water travels down a steep pipe called the ___3.",
     "4. It strikes the curved buckets of a ___4.",
     "5. Spent water leaves through the ___5."],
    [(1, "reservoir", "Water stored behind the dam forms a ______",
      "Water held behind the dam forms a reservoir",
      "PARAFFRAZ: stored = held."),
     (2, "head", "difference in level is called the ______",
      "the difference in level between its surface and the outlet "
      "is called the head", "Atama nomi."),
     (3, "penstock", "steep pipe called the ______",
      "travels down a steep pipe known as the penstock",
      "PARAFFRAZ: called = known as."),
     (4, "turbine", "curved buckets of a ______",
      "it strikes the curved buckets of a turbine",
      "Aylanuvchi qism."),
     (5, "tailrace", "leaves through the ______",
      "Spent water leaves through a wide channel called the "
      "tailrace", "Chiqish kanali.")],
))

# --------------------------------------------------------------- 17
PASSAGES.append(P(
    17, "A COMMERCIAL GREENHOUSE",
    "The structure is covered with twin-wall polycarbonate rather "
    "than glass, since the layer of air trapped between the two "
    "walls cuts heat loss by roughly forty percent. Along the ridge "
    "run motorised vents which open automatically when sensors "
    "detect that the air has passed twenty-six degrees. On the "
    "sunward side a movable screen, drawn across on wires, shades "
    "the crop at midday. Water reaches the plants through a drip "
    "line laid along each row, and carbon dioxide from the boiler "
    "flue is piped in to speed up growth rather than being released.",
    "A commercial greenhouse",
    ["1. The cover is made of twin-wall ___1.",
     "2. Trapped air cuts heat loss by about ___2.",
     "3. Motorised ___3 along the ridge open automatically.",
     "4. A movable ___4 shades the crop at midday.",
     "5. Plants are watered through a ___5 in each row."],
    [(1, "polycarbonate", "twin-wall ______",
      "covered with twin-wall polycarbonate rather than glass",
      "Material nomi. Chalg'ituvchi: «glass» — rad etilgan."),
     (2, "forty percent", "cuts heat loss by about ______",
      "cuts heat loss by roughly forty percent",
      "PARAFFRAZ: about = roughly. Chalg'ituvchi: 26 daraja."),
     (3, "vents", "Motorised ______ along the ridge",
      "Along the ridge run motorised vents which open "
      "automatically", "Shamollatish qismi."),
     (4, "screen", "A movable ______ shades the crop",
      "a movable screen, drawn across on wires, shades the crop",
      "Soyalash qurilmasi."),
     (5, "drip line", "watered through a ______",
      "Water reaches the plants through a drip line laid along each "
      "row", "Ikki so'zli javob.")],
))

# --------------------------------------------------------------- 18
PASSAGES.append(P(
    18, "A DESALINATION PLANT",
    "Seawater is first passed through a pre-treatment stage in which "
    "sand filters and cartridge filters remove particles that would "
    "otherwise block the membranes. A high-pressure pump then forces "
    "the water against a semi-permeable membrane at roughly sixty "
    "bar; pure water crosses it while salt is left behind. About "
    "forty percent of the intake emerges as fresh water, the rest "
    "leaving as brine. Because this brine is still under pressure, "
    "an energy recovery device captures that pressure and returns it "
    "to the incoming stream, cutting electricity use by up to half.",
    "A desalination plant",
    ["1. ___1 filters remove particles before the membranes.",
     "2. A high-pressure ___2 forces water against the membrane.",
     "3. The ___3 lets pure water through but holds back salt.",
     "4. The water that is left over is called ___4.",
     "5. An energy ___5 returns pressure to the incoming stream."],
    [(1, "Sand", "______ filters remove particles",
      "sand filters and cartridge filters remove particles",
      "Filtr turi."),
     (2, "pump", "A high-pressure ______ forces water",
      "A high-pressure pump then forces the water against a "
      "semi-permeable membrane", "Nasos."),
     (3, "membrane", "The ______ lets pure water through",
      "pure water crosses it while salt is left behind",
      "Yarim o'tkazuvchi qism."),
     (4, "brine", "left over is called ______",
      "the rest leaving as brine", "Chiqindi nomi."),
     (5, "recovery device",
      "An energy ______ returns pressure to the incoming stream",
      "an energy recovery device captures that pressure and returns "
      "it to the incoming stream",
      "Ikki so'z chegarasi: «energy» yorliqda berilgan, javob "
      "«recovery device».")],
))

# --------------------------------------------------------------- 19
PASSAGES.append(P(
    19, "A JET ENGINE",
    "Air is drawn in by a large fan at the front, and most of it "
    "bypasses the core entirely, providing the greater part of the "
    "thrust in a modern engine. The remainder enters the compressor, "
    "a series of ever-smaller blade stages that raise the pressure "
    "by a factor of about forty. In the combustor this compressed "
    "air is mixed with kerosene and burned continuously at "
    "temperatures above the melting point of the metal itself; the "
    "blades survive only because cool air is bled through tiny holes "
    "in their surface. The expanding gas then spins the turbine, "
    "which drives both the compressor and the fan through a common "
    "shaft, before leaving through the nozzle.",
    "A jet engine",
    ["1. Air is drawn in by a large ___1 at the front.",
     "2. The ___2 raises the pressure about forty times.",
     "3. Fuel is burned in the ___3.",
     "4. Blades survive because cool air passes through tiny ___4.",
     "5. Gas finally leaves through the ___5."],
    [(1, "fan", "drawn in by a large ______",
      "Air is drawn in by a large fan at the front", "Old qism."),
     (2, "compressor", "The ______ raises the pressure",
      "enters the compressor, a series of ever-smaller blade stages "
      "that raise the pressure", "Bosim oshiruvchi qism."),
     (3, "combustor", "Fuel is burned in the ______",
      "In the combustor this compressed air is mixed with kerosene "
      "and burned", "PARAFFRAZ: fuel = kerosene."),
     (4, "holes", "cool air passes through tiny ______",
      "cool air is bled through tiny holes in their surface",
      "PARAFFRAZ: passes through = is bled through."),
     (5, "nozzle", "leaves through the ______",
      "before leaving through the nozzle", "Chiqish qismi.")],
))

# --------------------------------------------------------------- 20
PASSAGES.append(P(
    20, "A SPACE STATION MODULE",
    "The outer wall is not a single skin but a Whipple shield: a thin "
    "sacrificial layer stands a few centimetres clear of the main "
    "hull, so that a particle striking it is vaporised rather than "
    "punching through. Inside, carbon dioxide is stripped from the "
    "air by beds of a mineral called zeolite, which release the gas "
    "overboard when heated. Water is recovered from humidity and "
    "urine alike, a system that now returns about ninety-three "
    "percent of what the crew consumes. Because there is no "
    "convection without gravity, fans must run constantly or exhaled "
    "air would form a pocket around a sleeping astronaut. Power "
    "arrives through a truss from solar arrays that rotate to follow "
    "the Sun.",
    "A space station module",
    ["1. The outer wall is a ___1 shield.",
     "2. Carbon dioxide is absorbed by a mineral called ___2.",
     "3. The water system recovers about ___3 of what is used.",
     "4. ___4 must run constantly because there is no convection.",
     "5. Power reaches the module along a ___5."],
    [(1, "Whipple", "The outer wall is a ______ shield",
      "The outer wall is not a single skin but a Whipple shield",
      "Qalqon nomi."),
     (2, "zeolite", "absorbed by a mineral called ______",
      "stripped from the air by beds of a mineral called zeolite",
      "PARAFFRAZ: absorbed = stripped."),
     (3, "ninety-three percent", "recovers about ______",
      "a system that now returns about ninety-three percent of what "
      "the crew consumes", "Ikki so'zli javob."),
     (4, "Fans", "______ must run constantly",
      "fans must run constantly or exhaled air would form a pocket",
      "Havo aylantiruvchi qism."),
     (5, "truss", "Power reaches the module along a ______",
      "Power arrives through a truss from solar arrays",
      "PARAFFRAZ: reaches ... along = arrives through.")],
))


# =====================================================================
#  YIG'ISH
# =====================================================================
ALT = {
    "recovery device": "energy recovery device",
    "ten minutes": "10 minutes",
    "forty percent": "40 percent",
    "ninety-three percent": "93 percent",
    "65 percent": "sixty-five percent",
    "210 passengers": "210",
    "160 km": "160 kilometres",
}


def _mask(line, keep):
    s = str(line)
    for k in range(1, 12):
        s = s.replace(f"___{k}", "______" if k == keep else "…")
    return s


def _cefr(level):
    if level <= 5:
        return "A2"
    if level <= 9:
        return "B1"
    if level <= 14:
        return "B2"
    return "C1"


def _prompt_for(labels, n, cue):
    mark = f"___{n}"
    for ln in labels:
        if mark in ln:
            return _mask(ln, n)
    return str(cue).replace("______", "______")


def build_rows():
    out = []
    for p in PASSAGES:
        for i, (n, ans, cue, psg, note) in enumerate(p["gaps"]):
            payload = {
                "title": p["title"],
                "passage": p["text"],
                "figure": p["figure"],
                "labels": [_mask(ln, n) for ln in p["labels"]],
                "gap_no": n,
                "in_table": False,
                "prompt": _prompt_for(p["labels"], n, cue),
                "step": p["level"],
                "order": i,
                "step_title": f"{p['level']}-daraja",
                "tip": "Qaysi qism ekanini toping",
                "instruction": ("Complete the labels on the diagram. "
                                "Choose NO MORE THAN TWO WORDS AND/OR "
                                "A NUMBER from the passage."),
            }
            explain = f"Yorliqda: «{cue}»  ->  Matnda: «{psg}». {note}"
            out.append((KIND, _cefr(p["level"]), payload, ans,
                        explain, ALT.get(ans, ""),
                        {"table": cue, "passage": psg}))
    return out


def seed_reading_label(db):
    """Idempotent: (kind, passage, gap_no) bo'yicha."""
    from common import _seed_done, _seed_mark
    if _seed_done(db, "ielts_read_label_v1"):
        return None
    import json
    import models

    have = set()
    for k, p in db.query(models.PracticeItem.kind,
                         models.PracticeItem.payload).filter(
            models.PracticeItem.skill == SKILL).all():
        try:
            pl = json.loads(p)
            have.add((k, pl.get("passage"), pl.get("gap_no")))
        except Exception:
            pass
    made = 0
    for kind, level, payload, answer, explain, alt, para in build_rows():
        key = (kind, payload["passage"], payload["gap_no"])
        if key in have:
            continue
        payload = dict(payload)
        payload["paraphrase"] = para
        db.add(models.PracticeItem(
            skill=SKILL, kind=kind, level=level,
            payload=json.dumps(payload, ensure_ascii=False),
            answer=answer, alt=alt or None, explain=explain))
        have.add(key)
        made += 1
    if made:
        db.commit()
    _seed_mark(db, "ielts_read_label_v1")
    return made
