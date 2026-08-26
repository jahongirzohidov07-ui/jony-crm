# -*- coding: utf-8 -*-
"""CEFR LISTENING 4-QISM — MAP LABELLING (2026-08-26).

Jahongir: "endi qolgan partlarga ham 100tadan tuzib qoy."

FORMAT (kitobdan): "You will hear someone giving a talk. Label
the places (1-5) on the map (A-H). There are extra options which
you do not need to use."

BOSHQA QISMLARDAN FARQI — MUHIM. 1, 2, 3, 5 va 6-qismlarda audio
matni Multilevel Master audioskriptidan AYNAN olingan. Bu qismda
esa bunday qilinmadi va buning sababi bor: kitobdagi xaritalar
RASM, ular skaner qilingan. Audio matnini olib xaritani taxmin
qilib chizsak, joylashuvlar mos kelmay qolishi mumkin edi — ya'ni
javobi noto'g'ri mashq chiqardi. Shuning uchun bu qismda xarita
ham, ma'ruza ham shu yerda tuzilgan. Ikkalasi bitta manbadan
chiqqani uchun har bir javobni test dasturiy yo'l bilan
tekshira oladi.

XARITA IKKI XIL. Kompas turi (bog', ferma, sayt) — 3x3 katak,
markazda belgi, atrofida A..H. Koridor turi (bino) — chapda uch
xona, o'ngda uch xona, G esa binoning boshqa joyida.
"""

SKILL = "ielts_listening"
KIND = "cefr_map"
RATE = 0.92

# Har harf xaritada qayerda turadi — test shu jadval bo'yicha
# ma'ruzadagi ifodaga mos kelishini tekshiradi.
COMPASS_POS = {
    'A': ['north-west'],
    'B': ['in the north', 'top of the map in the middle'],
    'C': ['north-east'],
    'D': ['western side'],
    'E': ['eastern side'],
    'F': ['south-west'],
    'G': ['due south'],
    'H': ['south-east'],
}
CORRIDOR_POS = {
    'A': ['first', 'nearest'],
    'B': ['middle one on the left', 'middle room on the left'],
    'C': ['far end on the left', 'very end of the corridor on the left'],
    'D': ['first', 'nearest'],
    'E': ['middle one on the right', 'middle room on the right'],
    'F': ['far end on the right', 'last one on the right', 'last room on the right'],
    'G': ['not', 'upstairs', 'across the road', 'top of the stairs', 'one floor up', 'ground floor'],
}


MAP_TIPS = [
    ('Bu mashq nima',
     "Ekranda xarita turadi, unda A dan H gacha joylar belgilangan. Ma'ruzachi joylarni tartib bilan aytadi — siz har bir joyni to'g'ri harf bilan moslashtirasiz. Ba'zi harflar ORTIQCHA.",
     ''),
    ("Avval o'zingizni xaritada toping",
     "Ma'ruza deyarli har doim «you are here» dan boshlanadi: kirish, qabulxona, darvoza. Shu nuqtani topmasangiz, «chapda» va «o'ngda» degan so'zlar ma'nosini yo'qotadi.",
     ''),
    ("Kompas so'zlarini yodda tuting",
     "north = tepa, south = past, west = chap, east = o'ng. «north-west corner» — tepa chap burchak. Bu to'rt so'z javoblarning yarmini beradi.",
     ''),
    ("«halfway up the map» — o'rta qator",
     "«on the eastern side, level with the lake» degani — o'ng tomonda, markaz bilan bir qatorda. Burchak emas.",
     ''),
    ('Koridorda tartib muhim',
     '«the first room on the left», «the middle one», «at the far end» — uchtasi uch xil xona. Faqat «left» yoki «right» ni eshitib qolmang, NECHANCHISI ekanini ham tuting.',
     ''),
    ("Ortiqcha harflar ataylab qo'yiladi",
     "Ma'ruzachi ko'pincha oxirida «bu joyga kirilmaydi» deb qolgan harflarni aytib o'tadi. Ular javob emas — lekin ularni eshitish sizga qolganini tasdiqlaydi.",
     ''),
    ("Joylar ma'ruza tartibida so'raladi",
     "1-savol birinchi aytilgan joy, 5-savol oxirgisi. Bittasini o'tkazib yuborsangiz, keyingisini kutib turing.",
     ''),
]


SITES = [
    {"no": 1, "title": 'OAK HILL COUNTRY PARK', "shape": 'compass',
     "figure": '                    N\n     ┌───────┬───────┬───────┐\n     │   A   │   B   │   C   │\n     ├───────┼───────┼───────┤\n  W  │   D   │ LAKE  │   E   │  E\n     ├───────┼───────┼───────┤\n     │   F   │   G   │   H   │\n     └───────┴───┬───┴───────┘\n              ENTRANCE\n                    S',
     "say": 'Welcome to Oak Hill Country Park. Let me show you where everything is on this plan before you set off. You have come in through the entrance at the bottom of the map, in the south. The lake is right in the middle, and all the paths lead round it. Now, the visitor centre, where you can pick up a leaflet, is immediately to your left as you come in, in the south-west corner. Straight across the park from there, in the far north-west corner, is the wild flower meadow, which is at its best in June. The bird hide is on the western side, exactly halfway up the map between the meadow and the visitor centre, and it looks out over the water. On the opposite side of the lake, on the eastern side, level with the bird hide, is the adventure playground for children. And finally the café, which serves hot food all day, is at the very top of the map, in the middle, in the north. Please note that the south-east corner is a working farm and is not open to visitors. Enjoy your visit.',
     "places": [
         ('the visitor centre', 'F'),
         ('the wild flower meadow', 'A'),
         ('the bird hide', 'D'),
         ('the adventure playground', 'E'),
         ('the café', 'B'),
     ]},
    {"no": 2, "title": 'RIVERSIDE SPORTS GROUND', "shape": 'compass',
     "figure": '                    N\n     ┌───────┬───────┬───────┐\n     │   A   │   B   │   C   │\n     ├───────┼───────┼───────┤\n  W  │   D   │ PITCH │   E   │  E\n     ├───────┼───────┼───────┤\n     │   F   │   G   │   H   │\n     └───────┴───┬───┴───────┘\n              ENTRANCE\n                    S',
     "say": 'Good morning, and welcome to Riverside Sports Ground. Here is the plan. You are standing at the entrance at the bottom of the map, and the main pitch is in the centre. Let me point out five things. The changing rooms are in the north-west corner, at the top of the map on the left, so allow a few minutes to walk there. The car park is directly opposite the entrance, at the top of the map in the middle, in the north. The tennis courts are on the eastern side, level with the main pitch, halfway up the map. The clubhouse, where refreshments are served, is in the south-east corner, on your right as you come in. And the equipment store is in the south-west corner, on your left as you come in. The north-east corner and the western side are still under construction, so please keep away from them.',
     "places": [
         ('the changing rooms', 'A'),
         ('the car park', 'B'),
         ('the tennis courts', 'E'),
         ('the clubhouse', 'H'),
         ('the equipment store', 'F'),
     ]},
    {"no": 3, "title": 'LAKESIDE CAMPUS', "shape": 'compass',
     "figure": '                    N\n     ┌───────┬───────┬───────┐\n     │   A   │   B   │   C   │\n     ├───────┼───────┼───────┤\n  W  │   D   │SQUARE │   E   │  E\n     ├───────┼───────┼───────┤\n     │   F   │   G   │   H   │\n     └───────┴───┬───┴───────┘\n              ENTRANCE\n                    S',
     "say": 'Let me help you find your way around Lakeside Campus. You are at the entrance at the bottom of the plan, and the central square is in the middle. The library is the large building at the top of the map, in the middle, directly opposite the entrance. The science block is in the north-east corner, to the right of the library. The student residences are on the western side, halfway up the map, next to the square. The sports hall is in the south-east corner, so it is on your right as you walk in. And the medical centre is in the north-west corner, at the top left, which is the quietest part of the campus. The area at the bottom left and the area to the east of the square are car parks and are not marked on your plan.',
     "places": [
         ('the library', 'B'),
         ('the science block', 'C'),
         ('the student residences', 'D'),
         ('the sports hall', 'H'),
         ('the medical centre', 'A'),
     ]},
    {"no": 4, "title": 'MARSH FARM VISITOR TRAIL', "shape": 'compass',
     "figure": '                    N\n     ┌───────┬───────┬───────┐\n     │   A   │   B   │   C   │\n     ├───────┼───────┼───────┤\n  W  │   D   │ BARN  │   E   │  E\n     ├───────┼───────┼───────┤\n     │   F   │   G   │   H   │\n     └───────┴───┬───┴───────┘\n              ENTRANCE\n                    S',
     "say": 'Hello everyone, and welcome to Marsh Farm. Look at the trail map for a moment. You have arrived at the entrance in the south, and the old barn stands in the centre of the farm. Five places you will want to find. The milking parlour is on the eastern side, level with the barn, halfway up the map. The duck pond is in the north-west corner, right at the top on the left. The farm shop is in the south-east corner, so you will pass it on your right on the way out. The play barn for children is at the top of the map in the middle, in the north. And the picnic area is on the western side, level with the barn, opposite the milking parlour. Please do not go into the north-east corner or the south-west corner: those fields are in use.',
     "places": [
         ('the milking parlour', 'E'),
         ('the duck pond', 'A'),
         ('the farm shop', 'H'),
         ('the play barn', 'B'),
         ('the picnic area', 'D'),
     ]},
    {"no": 5, "title": 'THE OLD HARBOUR', "shape": 'compass',
     "figure": '                    N\n     ┌───────┬───────┬───────┐\n     │   A   │   B   │   C   │\n     ├───────┼───────┼───────┤\n  W  │   D   │HARBOUR│   E   │  E\n     ├───────┼───────┼───────┤\n     │   F   │   G   │   H   │\n     └───────┴───┬───┴───────┘\n              ENTRANCE\n                    S',
     "say": 'Right, this is a map of the old harbour area. You are standing at the entrance to the quayside, at the bottom of the map, and the harbour itself is in the middle. The lighthouse is at the very top of the map, in the middle, in the north, and you can see it from anywhere in the town. The fish market is in the north-west corner, at the top on the left, and it opens at five in the morning. The lifeboat station is on the eastern side, level with the harbour, halfway up the map. The maritime museum is in the south-west corner, on your left as you come in. And the ferry terminal is in the south-east corner, on your right. The north-east corner is a boatyard and the western side next to the museum is closed for repairs.',
     "places": [
         ('the lighthouse', 'B'),
         ('the fish market', 'A'),
         ('the lifeboat station', 'E'),
         ('the maritime museum', 'F'),
         ('the ferry terminal', 'H'),
     ]},
    {"no": 6, "title": 'GREENFIELD GARDEN CENTRE', "shape": 'compass',
     "figure": '                    N\n     ┌───────┬───────┬───────┐\n     │   A   │   B   │   C   │\n     ├───────┼───────┼───────┤\n  W  │   D   │ GLASS │   E   │  E\n     ├───────┼───────┼───────┤\n     │   F   │   G   │   H   │\n     └───────┴───┬───┴───────┘\n              ENTRANCE\n                    S',
     "say": 'Welcome to Greenfield Garden Centre. Here is the site plan. The entrance is at the bottom, and the big glasshouse is in the centre. The tool shop is in the north-east corner, right at the top on the right. The seed counter is on the western side, level with the glasshouse, halfway up the map. The tree nursery takes up the whole of the north, at the top of the map in the middle. The coffee shop is in the south-east corner, so it is the last thing you pass on the way out. And the delivery bay is in the south-west corner, where the lorries come in. The north-west corner is staff parking and the eastern side next to the glasshouse is a storage yard.',
     "places": [
         ('the tool shop', 'C'),
         ('the seed counter', 'D'),
         ('the tree nursery', 'B'),
         ('the coffee shop', 'H'),
         ('the delivery bay', 'F'),
     ]},
    {"no": 7, "title": 'HILLTOP ZOO', "shape": 'compass',
     "figure": '                    N\n     ┌───────┬───────┬───────┐\n     │   A   │   B   │   C   │\n     ├───────┼───────┼───────┤\n  W  │   D   │AVIARY │   E   │  E\n     ├───────┼───────┼───────┤\n     │   F   │   G   │   H   │\n     └───────┴───┬───┴───────┘\n              ENTRANCE\n                    S',
     "say": "Good afternoon and welcome to Hilltop Zoo. Take a look at the map. You come in at the entrance in the south, and the great aviary is in the middle of the zoo. The elephant house is at the top of the map, in the middle, in the north, and feeding time there is at four o'clock. The reptile house is in the north-west corner. The penguin pool is on the eastern side, level with the aviary, halfway up the map. The gift shop is in the south-west corner, on your left as you arrive. And the education centre, where the school groups go, is in the south-east corner. The north-east corner and the western side beside the aviary are keepers' areas and are closed to the public.",
     "places": [
         ('the elephant house', 'B'),
         ('the reptile house', 'A'),
         ('the penguin pool', 'E'),
         ('the gift shop', 'F'),
         ('the education centre', 'H'),
     ]},
    {"no": 8, "title": 'SUMMER FESTIVAL SITE', "shape": 'compass',
     "figure": '                    N\n     ┌───────┬───────┬───────┐\n     │   A   │   B   │   C   │\n     ├───────┼───────┼───────┤\n  W  │   D   │ STAGE │   E   │  E\n     ├───────┼───────┼───────┤\n     │   F   │   G   │   H   │\n     └───────┴───┬───┴───────┘\n              ENTRANCE\n                    S',
     "say": 'Hello, and welcome to the summer festival. Let me run through the site map with you. The entrance is at the bottom, in the south, and the main stage is in the centre. The food court is at the top of the map, in the middle, in the north, so it is the furthest point from the gate. The camping field is in the north-west corner. The first aid tent is on the eastern side, level with the stage, halfway up the map, and it is open all night. The information point is in the south-west corner, immediately on your left as you come in. And the craft market is in the south-east corner, immediately on your right. The north-east corner is for staff vehicles and the area west of the stage is a quiet zone.',
     "places": [
         ('the food court', 'B'),
         ('the camping field', 'A'),
         ('the first aid tent', 'E'),
         ('the information point', 'F'),
         ('the craft market', 'H'),
     ]},
    {"no": 9, "title": 'NORTHGATE SHOPPING CENTRE', "shape": 'corridor',
     "figure": '        ENTRANCE / RECEPTION\n                 │\n   ┌───────┬───────┬───────┐\n   │   A   │   B   │   C   │   ← left side\n   ├───────┴───────┴───────┤\n   │ ─────  CORRIDOR  ──── │\n   ├───────┬───────┬───────┤\n   │   D   │   E   │   F   │   ← right side\n   └───────┴───────┴───────┘\n     1st     2nd     far end\n        G = across the road, opposite reception',
     "say": 'Let me explain the layout of Northgate Shopping Centre. You are standing at reception at the near end of the long corridor. Shops are on both sides. On the left-hand side, the first unit you come to is the bookshop. The second unit on the left is the pharmacy, and the third one, right at the far end on the left, is the shoe shop. Now on the right-hand side: the first unit on the right is the bakery, the second one on the right is the post office, and the last one on the right, at the far end, is the bank. Finally, the car park is not inside the building at all; it is across the road, directly opposite reception. Please remember that the units are numbered from the reception end.',
     "places": [
         ('the bookshop', 'A'),
         ('the shoe shop', 'C'),
         ('the bakery', 'D'),
         ('the bank', 'F'),
         ('the car park', 'G'),
     ]},
    {"no": 10, "title": 'THE ARTS CENTRE — ground floor', "shape": 'corridor',
     "figure": '        ENTRANCE / RECEPTION\n                 │\n   ┌───────┬───────┬───────┐\n   │   A   │   B   │   C   │   ← left side\n   ├───────┴───────┴───────┤\n   │ ─────  CORRIDOR  ──── │\n   ├───────┬───────┬───────┤\n   │   D   │   E   │   F   │   ← right side\n   └───────┴───────┴───────┘\n     1st     2nd     far end\n        G = upstairs, above reception',
     "say": 'Now a word about the ground floor of the Arts Centre. We are standing at reception, and the corridor runs straight ahead of us. Taking the left-hand side first: the room nearest to us on the left is the box office. Next to it, the middle room on the left, is the rehearsal room. The room at the very end of the corridor on the left is the costume store. On the right-hand side, the room nearest to us is the gallery, the middle room on the right is the recording studio, and the room at the far end on the right is the workshop. The staff canteen is not on this floor at all — it is upstairs, directly above reception. Please do not go into the costume store without asking.',
     "places": [
         ('the box office', 'A'),
         ('the costume store', 'C'),
         ('the gallery', 'D'),
         ('the workshop', 'F'),
         ('the staff canteen', 'G'),
     ]},
    {"no": 11, "title": 'BRIDGE STREET LIBRARY — first floor', "shape": 'corridor',
     "figure": '        ENTRANCE / RECEPTION\n                 │\n   ┌───────┬───────┬───────┐\n   │   A   │   B   │   C   │   ← left side\n   ├───────┴───────┴───────┤\n   │ ─────  CORRIDOR  ──── │\n   ├───────┬───────┬───────┤\n   │   D   │   E   │   F   │   ← right side\n   └───────┴───────┴───────┘\n     1st     2nd     far end\n        G = ground floor, beside the main door',
     "say": "Let me tell you where things are on the first floor of the library. You come up the stairs and the corridor runs away from you. On the left-hand side there are three rooms. The first one on the left is the children's room, the middle one on the left is the local history room, and the one at the far end on the left is the computer room. On the right-hand side, the first room is the quiet study area, the middle one on the right is the meeting room, and the last one on the right is the photocopying room. The returns desk is not up here — it is downstairs on the ground floor, beside the main door, so please return your books there.",
     "places": [
         ("the children's room", 'A'),
         ('the computer room', 'C'),
         ('the quiet study area', 'D'),
         ('the photocopying room', 'F'),
         ('the returns desk', 'G'),
     ]},
    {"no": 12, "title": 'SEAVIEW HOLIDAY VILLAGE', "shape": 'compass',
     "figure": '                    N\n     ┌───────┬───────┬───────┐\n     │   A   │   B   │   C   │\n     ├───────┼───────┼───────┤\n  W  │   D   │ POOL  │   E   │  E\n     ├───────┼───────┼───────┤\n     │   F   │   G   │   H   │\n     └───────┴───┬───┴───────┘\n              ENTRANCE\n                    S',
     "say": "Welcome to Seaview Holiday Village. Here is your site map. You arrive at the entrance in the south and the swimming pool is in the centre. The restaurant is at the top of the map in the middle, in the north, with a view over the sea. The children's club is in the north-west corner, well away from the road. The bike hire is on the eastern side, level with the pool, halfway up the map. The laundry is in the south-west corner, next to the entrance on your left. And the mini-market is in the south-east corner, on your right as you drive in. The north-east corner is the staff village and the western strip beside the pool is a garden.",
     "places": [
         ('the restaurant', 'B'),
         ("the children's club", 'A'),
         ('the bike hire', 'E'),
         ('the laundry', 'F'),
         ('the mini-market', 'H'),
     ]},
    {"no": 13, "title": 'WESTFIELD BUSINESS PARK', "shape": 'compass',
     "figure": '                    N\n     ┌───────┬───────┬───────┐\n     │   A   │   B   │   C   │\n     ├───────┼───────┼───────┤\n  W  │   D   │ PLAZA │   E   │  E\n     ├───────┼───────┼───────┤\n     │   F   │   G   │   H   │\n     └───────┴───┬───┴───────┘\n              ENTRANCE\n                    S',
     "say": "This is the plan of Westfield Business Park. Vehicles come in at the entrance in the south and the central plaza is in the middle. The conference centre is at the top of the map in the middle, in the north. The research laboratory is in the north-east corner, furthest from the road. The staff gym is on the western side, level with the plaza, halfway up the map. The security office is in the south-west corner, right beside the entrance. And the visitors' car park is in the south-east corner. Deliveries use the north-west corner and the strip east of the plaza, so please do not park there.",
     "places": [
         ('the conference centre', 'B'),
         ('the research laboratory', 'C'),
         ('the staff gym', 'D'),
         ('the security office', 'F'),
         ("the visitors' car park", 'H'),
     ]},
    {"no": 14, "title": 'MOORLAND WALKING CENTRE', "shape": 'compass',
     "figure": '                    N\n     ┌───────┬───────┬───────┐\n     │   A   │   B   │   C   │\n     ├───────┼───────┼───────┤\n  W  │   D   │CAR PK │   E   │  E\n     ├───────┼───────┼───────┤\n     │   F   │   G   │   H   │\n     └───────┴───┬───┴───────┘\n              ENTRANCE\n                    S',
     "say": "Before you set off, look at the plan of the walking centre. The gate is at the bottom, in the south, and the car park is in the middle. The youth hostel is at the top of the map in the middle, in the north. The map room, where you can check the weather, is in the north-west corner. The equipment hire is on the eastern side, level with the car park, halfway up the map. The camp site is in the south-east corner, close to the gate. And the warden's house is in the south-west corner. The north-east corner is private woodland and the strip west of the car park is a stream, so take care.",
     "places": [
         ('the youth hostel', 'B'),
         ('the map room', 'A'),
         ('the equipment hire', 'E'),
         ('the camp site', 'H'),
         ("the warden's house", 'F'),
     ]},
    {"no": 15, "title": 'CITY BOTANIC GARDENS', "shape": 'compass',
     "figure": '                    N\n     ┌───────┬───────┬───────┐\n     │   A   │   B   │   C   │\n     ├───────┼───────┼───────┤\n  W  │   D   │ FOUNT │   E   │  E\n     ├───────┼───────┼───────┤\n     │   F   │   G   │   H   │\n     └───────┴───┬───┴───────┘\n              ENTRANCE\n                    S',
     "say": 'Here is the plan of the Botanic Gardens. You come in at the south gate at the bottom and the fountain is in the very centre. The tropical house is at the top of the map in the middle, in the north. The rock garden is in the north-west corner. The rose walk runs along the eastern side, level with the fountain, halfway up the map. The plant shop is in the south-west corner, just inside the gate on your left. And the tea garden is in the south-east corner, on your right. The north-east corner holds the seed store and the strip west of the fountain is a lawn where you may sit.',
     "places": [
         ('the tropical house', 'B'),
         ('the rock garden', 'A'),
         ('the rose walk', 'E'),
         ('the plant shop', 'F'),
         ('the tea garden', 'H'),
     ]},
    {"no": 16, "title": 'STONEBRIDGE MUSEUM — lower floor', "shape": 'corridor',
     "figure": '        ENTRANCE / RECEPTION\n                 │\n   ┌───────┬───────┬───────┐\n   │   A   │   B   │   C   │   ← left side\n   ├───────┴───────┴───────┤\n   │ ─────  CORRIDOR  ──── │\n   ├───────┬───────┬───────┤\n   │   D   │   E   │   F   │   ← right side\n   └───────┴───────┴───────┘\n     1st     2nd     far end\n        G = at the top of the stairs',
     "say": 'Let me explain the lower floor of the museum. At the bottom of the stairs a long corridor runs ahead of you, with rooms on both sides. On the left, the first room is the cloakroom, the middle room on the left is the film room, and the room at the far end on the left is the archive. On the right-hand side, the first room is the schools room, the middle room on the right is the restaurant, and the room at the far end on the right is the lecture theatre. The shop is not down here at all — you will find it at the top of the stairs as you leave. Please note that the archive can only be visited by appointment.',
     "places": [
         ('the cloakroom', 'A'),
         ('the archive', 'C'),
         ('the schools room', 'D'),
         ('the lecture theatre', 'F'),
         ('the shop', 'G'),
     ]},
    {"no": 17, "title": 'AIRPORT TERMINAL TWO', "shape": 'corridor',
     "figure": '        ENTRANCE / RECEPTION\n                 │\n   ┌───────┬───────┬───────┐\n   │   A   │   B   │   C   │   ← left side\n   ├───────┴───────┴───────┤\n   │ ─────  CORRIDOR  ──── │\n   ├───────┬───────┬───────┤\n   │   D   │   E   │   F   │   ← right side\n   └───────┴───────┴───────┘\n     1st     2nd     far end\n        G = one floor up, above check-in',
     "say": 'This is the layout of Terminal Two. You come in at check-in and the concourse runs straight ahead. On the left-hand side, the first area is the currency exchange, the middle one on the left is the pharmacy, and the far end on the left is the left-luggage office. On the right-hand side, the first area is the information desk, the middle one on the right is the bookshop, and the far end on the right is the car hire desk. The business lounge is not on this level; it is one floor up, directly above check-in. Passengers with hand baggage only should go straight to the far end.',
     "places": [
         ('the currency exchange', 'A'),
         ('the left-luggage office', 'C'),
         ('the information desk', 'D'),
         ('the car hire desk', 'F'),
         ('the business lounge', 'G'),
     ]},
    {"no": 18, "title": 'RIVERBANK NATURE RESERVE', "shape": 'compass',
     "figure": '                    N\n     ┌───────┬───────┬───────┐\n     │   A   │   B   │   C   │\n     ├───────┼───────┼───────┤\n  W  │   D   │ HIDE  │   E   │  E\n     ├───────┼───────┼───────┤\n     │   F   │   G   │   H   │\n     └───────┴───┬───┴───────┘\n              ENTRANCE\n                    S',
     "say": "Welcome to Riverbank Nature Reserve. Look at the plan. The entrance is at the bottom, in the south, and the main hide is in the middle. The heron pool is at the top of the map in the middle, in the north. The reed bed is in the north-west corner. The boardwalk runs along the eastern side, level with the hide, halfway up the map. The warden's hut is in the south-west corner, just inside the entrance. And the wildflower bank is in the south-east corner. The north-east corner is flooded most of the year and the strip west of the hide is fenced off for nesting birds.",
     "places": [
         ('the heron pool', 'B'),
         ('the reed bed', 'A'),
         ('the boardwalk', 'E'),
         ("the warden's hut", 'F'),
         ('the wildflower bank', 'H'),
     ]},
    {"no": 19, "title": 'HARVEST FOOD MARKET', "shape": 'compass',
     "figure": '                    N\n     ┌───────┬───────┬───────┐\n     │   A   │   B   │   C   │\n     ├───────┼───────┼───────┤\n  W  │   D   │SQUARE │   E   │  E\n     ├───────┼───────┼───────┤\n     │   F   │   G   │   H   │\n     └───────┴───┬───┴───────┘\n              ENTRANCE\n                    S',
     "say": 'Here is the plan of the food market. Shoppers come in from the south and the covered square is in the middle. The bakery stalls are at the top of the map in the middle, in the north. The cheese hall is in the north-west corner. The fish counters run along the eastern side, level with the square, halfway up the map. The flower stalls are in the south-west corner, the first thing you see as you come in. And the seating area is in the south-east corner. The north-east corner is used for deliveries and the strip west of the square is where the traders keep their vans.',
     "places": [
         ('the bakery stalls', 'B'),
         ('the cheese hall', 'A'),
         ('the fish counters', 'E'),
         ('the flower stalls', 'F'),
         ('the seating area', 'H'),
     ]},
    {"no": 20, "title": 'PINEWOOD ACTIVITY CAMP', "shape": 'compass',
     "figure": '                    N\n     ┌───────┬───────┬───────┐\n     │   A   │   B   │   C   │\n     ├───────┼───────┼───────┤\n  W  │   D   │ FIRE  │   E   │  E\n     ├───────┼───────┼───────┤\n     │   F   │   G   │   H   │\n     └───────┴───┬───┴───────┘\n              ENTRANCE\n                    S',
     "say": 'Right, this is the plan of Pinewood Activity Camp. You arrive at the gate in the south and the camp fire circle is in the centre. The dining hall is at the top of the map in the middle, in the north. The climbing wall is in the north-west corner. The archery range is on the eastern side, level with the fire circle, halfway up the map. The first aid room is in the south-west corner, beside the gate. And the boat store is in the south-east corner, nearest the water. The north-east corner is where the tents are pitched and the strip west of the fire circle is kept clear for safety.',
     "places": [
         ('the dining hall', 'B'),
         ('the climbing wall', 'A'),
         ('the archery range', 'E'),
         ('the first aid room', 'F'),
         ('the boat store', 'H'),
     ]},
]


def build_rows():
    """(kind, level, payload, answer, explain, alt, paraphrase)."""
    out = []
    LET = ["A", "B", "C", "D", "E", "F", "G", "H"]
    for e, s in enumerate(SITES):
        step = 1 + e // 4
        opts = [l for l in LET if l in s["figure"]]
        for qi, (name, let) in enumerate(s["places"], 1):
            expl = (f"To'g'ri javob: {let} — {name}. "
                    f"Ma'ruzada aynan shu joy tasvirlangan.")
            out.append((
                KIND, step,
                {"say": s["say"],
                 "rate": RATE,
                 "figure": s["figure"],
                 "options": opts,
                 "prompt": f"{s['title']}  —  Where is {name}?",
                 "step": step,
                 "order": s["no"] * 10 + qi,
                 "hint": "Xaritadagi harfni tanlang",
                 "plays": 1,
                 "gap_ms": 1500},
                let, expl, None, None))
    return out


def seed_map(db):
    """Idempotent: bor bo'lsa qayta yozmaydi (hech narsa o'chmaydi)."""
    import json as _json
    import models
    have = {
        (_json.loads(r.payload).get("step"),
         _json.loads(r.payload).get("order"))
        for r in db.query(models.PracticeItem)
        .filter(models.PracticeItem.skill == SKILL,
                models.PracticeItem.kind == KIND).all()}
    n = 0
    for kind, step, payload, answer, explain, alt, para in build_rows():
        if (payload["step"], payload["order"]) in have:
            continue
        db.add(models.PracticeItem(
            skill=SKILL, kind=kind, level=step,
            payload=_json.dumps(payload, ensure_ascii=False),
            answer=answer, alt=alt, explain=explain, is_active=1))
        n += 1
    if n:
        db.commit()
    return n
