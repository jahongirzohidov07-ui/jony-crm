# -*- coding: utf-8 -*-
# =====================================================================
#  PLACEMENT TEST — READING BANKI
#
#  Har daraja uchun 3 ta matn, har matnga 2 ta savol. Bitta ekranda
#  matn va ikkala savol birga chiqadi, vaqt 90 soniya.
#
#  Matnlar uzunligi daraja bilan o'sadi: A1 ~40 so'z, C1 ~190 so'z.
#  Savollar ataylab matndan so'z ko'chirib topiladigan qilib emas,
#  MA'NOni tushunishni talab qiladigan qilib yozilgan — aks holda
#  o'qimasdan ham topib ketish mumkin bo'lardi.
#
#  To'g'ri javob ("a") SERVERDA qoladi, mijozga yuborilmaydi.
# =====================================================================

READ_ITEMS = [
    # ---------------- A1 ----------------
    {"id": 2001, "level": "A1", "secs": 60,
     "text": "Tom is nine years old. He lives in a small house with his "
             "mother, his father and his dog, Max. Tom goes to school by "
             "bus every morning. He likes maths, but he does not like "
             "English. After school he plays football with his friends.",
     "qs": [{"q": "How does Tom go to school?",
             "opts": ["By bus", "On foot", "By car", "By bike"], "a": 0},
            {"q": "Which subject does Tom NOT like?",
             "opts": ["Maths", "English", "Football", "Science"], "a": 1}]},
    {"id": 2002, "level": "A1", "secs": 60,
     "text": "The shop opens at nine o'clock in the morning and closes at "
             "six in the evening. On Sunday it is closed all day. You can "
             "buy bread, milk and fruit there. The shop is next to the "
             "post office.",
     "qs": [{"q": "When is the shop closed all day?",
             "opts": ["Monday", "Saturday", "Sunday", "Friday"], "a": 2},
            {"q": "What is next to the shop?",
             "opts": ["A school", "A hospital", "The post office",
                      "A bank"], "a": 2}]},
    {"id": 2003, "level": "A1", "secs": 60,
     "text": "Anna has got two cats. Their names are Luna and Coco. Luna "
             "is black and very small. Coco is white and big. Anna gives "
             "them milk every evening. The cats sleep on Anna's bed at "
             "night.",
     "qs": [{"q": "What colour is Coco?",
             "opts": ["Black", "White", "Grey", "Brown"], "a": 1},
            {"q": "Where do the cats sleep?",
             "opts": ["In the kitchen", "On Anna's bed", "In the garden",
                      "Under the table"], "a": 1}]},

    # ---------------- A2 ----------------
    {"id": 2101, "level": "A2", "secs": 75,
     "text": "Last summer my family went camping in the mountains for the "
             "first time. We put up our tent near a small river. The first "
             "night was very cold and nobody slept well, so the next day "
             "we bought two extra blankets in the village. After that the "
             "trip was wonderful. We cooked outside, swam in the river and "
             "walked for hours. We are going back next year.",
     "qs": [{"q": "Why did they buy blankets?",
             "opts": ["Because they lost their tent",
                      "Because the first night was cold",
                      "Because it rained",
                      "Because the village was cheap"], "a": 1},
            {"q": "How does the writer feel about the trip?",
             "opts": ["Disappointed", "Worried",
                      "Happy, and wants to return", "Bored"], "a": 2}]},
    {"id": 2102, "level": "A2", "secs": 75,
     "text": "Dear Mr Brown, I am writing about the jacket I ordered on "
             "3 March. It arrived yesterday, but it is the wrong size. I "
             "ordered a medium and you sent me a small. I would like to "
             "exchange it for the correct size. I have kept the receipt "
             "and the box. Please tell me where I should send the jacket. "
             "Yours sincerely, Elena Petrova",
     "qs": [{"q": "What is the problem?",
             "opts": ["The jacket is damaged",
                      "The jacket is the wrong size",
                      "The jacket never arrived",
                      "The jacket is too expensive"], "a": 1},
            {"q": "What does Elena want?",
             "opts": ["Her money back",
                      "An exchange for the right size",
                      "A discount", "An apology"], "a": 1}]},
    {"id": 2103, "level": "A2", "secs": 75,
     "text": "The city library has changed its opening hours. From "
             "1 September it will open at 8 a.m. instead of 10 a.m., and "
             "it will stay open until 8 p.m. on weekdays. However, it will "
             "now be closed on Saturdays. Students say the earlier opening "
             "is useful before lessons, but many families are unhappy "
             "because Saturday was the only day they could visit together.",
     "qs": [{"q": "What is new from 1 September?",
             "opts": ["It opens earlier",
                      "It closes earlier on weekdays",
                      "It opens on Sundays", "It has moved"], "a": 0},
            {"q": "Why are some families unhappy?",
             "opts": ["The books are old",
                      "It is closed on Saturdays",
                      "It is too far away", "It costs money"], "a": 1}]},

    # ---------------- B1 ----------------
    {"id": 2201, "level": "B1", "secs": 90,
     "text": "When Maria opened her small bakery five years ago, she "
             "expected most of her customers to come in the morning. In "
             "fact, the busiest time turned out to be between four and six "
             "in the afternoon, when parents collected their children from "
             "the school across the road. Maria quickly changed her plans: "
             "she began baking a second batch of bread at two o'clock and "
             "added small, cheap cakes that children could buy with their "
             "own pocket money. Her morning trade is still steady, but the "
             "afternoon now brings in almost twice as much. \"You can plan "
             "everything,\" she says, \"but the street tells you what it "
             "actually wants.\"",
     "qs": [{"q": "Why is the afternoon the busiest time?",
             "opts": ["Bread is cheaper then",
                      "Parents collect children from the school opposite",
                      "The bakery opens late",
                      "Tourists visit in the afternoon"], "a": 1},
            {"q": "What does Maria mean by her final sentence?",
             "opts": ["Planning is a waste of time",
                      "Customers should be told what to buy",
                      "Real customers may differ from what you planned",
                      "The street outside is too noisy"], "a": 2}]},
    {"id": 2202, "level": "B1", "secs": 90,
     "text": "Many people believe that they work better late at night. "
             "Research suggests that this is true for only a small number "
             "of adults. For most of us, the feeling of being productive "
             "after midnight comes from having fewer interruptions rather "
             "than from any real increase in mental ability. In fact, "
             "tests show that accuracy falls sharply after sixteen hours "
             "awake. The practical conclusion is not that night work is "
             "impossible, but that the quiet is what helps - and quiet can "
             "also be created earlier in the day.",
     "qs": [{"q": "Why do most people feel productive at night?",
             "opts": ["Their brains work faster",
                      "There are fewer interruptions",
                      "They have more energy",
                      "They need less sleep"], "a": 1},
            {"q": "What does the writer suggest?",
             "opts": ["Everyone should work at night",
                      "Night work is impossible",
                      "Quiet can be found at other times too",
                      "Sixteen hours of work is ideal"], "a": 2}]},
    {"id": 2203, "level": "B1", "secs": 90,
     "text": "The council's plan to close the car park in the town centre "
             "has divided residents. Shop owners argue that without "
             "parking, customers will drive to the large shopping centre "
             "outside town, and small businesses will suffer. Supporters "
             "of the plan point to three other towns where a similar "
             "change increased the number of people walking through the "
             "centre by more than a third. What both sides agree on is "
             "that the bus service must improve first. At present, only "
             "two routes serve the centre and neither runs after seven in "
             "the evening.",
     "qs": [{"q": "What do shop owners fear?",
             "opts": ["Buses will become too expensive",
                      "Customers will shop outside town",
                      "The council will raise taxes",
                      "Walking in the centre is dangerous"], "a": 1},
            {"q": "What do both sides agree about?",
             "opts": ["The car park should stay",
                      "The car park should close",
                      "Bus services need improving first",
                      "Other towns are not comparable"], "a": 2}]},

    # ---------------- B1+ ----------------
    {"id": 2301, "level": "B1+", "secs": 95,
     "text": "For years, employers assumed that offering fruit, table "
             "tennis and free coffee would keep staff happy. A recent "
             "survey of 4,000 workers suggests otherwise. When asked what "
             "would most improve their working life, only 6 per cent "
             "mentioned office facilities. Far higher on the list were "
             "predictable hours (34 per cent) and a manager who explained "
             "decisions (29 per cent). The authors note that perks are "
             "visible and easy to advertise, whereas good management is "
             "neither. This may explain why companies continue to invest "
             "in the former while the latter, which costs almost nothing, "
             "is often neglected. Employees, the report concludes, are not "
             "asking for luxury; they are asking to be able to plan their "
             "own lives.",
     "qs": [{"q": "What did the survey find?",
             "opts": ["Workers value free food most of all",
                      "Workers want predictable hours and clear management",
                      "Workers want higher pay above everything",
                      "Workers dislike their colleagues"], "a": 1},
            {"q": "Why do companies keep investing in perks?",
             "opts": ["They are cheaper than management training",
                      "They are visible and easy to advertise",
                      "Employees demand them in writing",
                      "They are proven to increase productivity"], "a": 1}]},
    {"id": 2302, "level": "B1+", "secs": 95,
     "text": "Repairing a broken appliance used to be ordinary. Today it "
             "is often cheaper to buy a new one, partly because "
             "manufacturers design products that are difficult to open and "
             "partly because spare parts are expensive or simply "
             "unavailable. Several countries have now introduced \"right "
             "to repair\" rules, requiring makers to supply parts for up "
             "to ten years and to publish repair manuals. Early results "
             "are modest but encouraging: in one country, the number of "
             "washing machines repaired rather than replaced rose by 12 "
             "per cent in two years. Critics argue that the rules raise "
             "prices slightly. Supporters reply that this is the true "
             "cost, previously paid by landfill sites rather than by "
             "consumers.",
     "qs": [{"q": "Why is repair often not worthwhile today?",
             "opts": ["Repairers are badly trained",
                      "Products are hard to open and parts are costly",
                      "People simply prefer newer designs",
                      "Repairing is against the law"], "a": 1},
            {"q": "How do supporters answer the criticism about prices?",
             "opts": ["Prices have not risen at all",
                      "The rules will soon be removed",
                      "The extra cost was previously paid by the "
                      "environment",
                      "Consumers do not notice small rises"], "a": 2}]},
    {"id": 2303, "level": "B1+", "secs": 95,
     "text": "Museums have spent two decades adding screens, apps and "
             "interactive games to their galleries. Visitor numbers rose, "
             "but a study tracking eye movement found something "
             "unexpected: in rooms with screens, visitors looked at the "
             "actual objects for an average of eight seconds, compared "
             "with twenty-three seconds in rooms without them. The "
             "researchers are careful not to conclude that technology is "
             "harmful. They point out that many of those visitors would "
             "not have entered the museum at all without it. The question, "
             "they suggest, is not whether to use screens but where to put "
             "them - perhaps at the entrance and the exit, rather than "
             "beside the exhibits themselves.",
     "qs": [{"q": "What did the eye-tracking study find?",
             "opts": ["Visitors ignored the screens completely",
                      "Visitors spent less time looking at objects near "
                      "screens",
                      "Visitors stayed longer in the museum overall",
                      "Visitors preferred the older exhibits"], "a": 1},
            {"q": "What do the researchers recommend?",
             "opts": ["Removing all technology from galleries",
                      "Placing screens away from the exhibits",
                      "Increasing the number of screens",
                      "Closing the interactive rooms"], "a": 1}]},

    # ---------------- B2 ----------------
    {"id": 2401, "level": "B2", "secs": 105,
     "text": "The notion that a language dies when its last fluent speaker "
             "does is intuitive but misleading. Long before that point, a "
             "language typically ceases to be transmitted to children, and "
             "from then on its fate is effectively settled, however many "
             "elderly speakers remain. Revitalisation efforts that "
             "concentrate on recording the final speakers therefore arrive "
             "too late to change the outcome, although they may preserve "
             "valuable material for scholarship. The programmes that have "
             "succeeded - in Wales, in Hawai'i, among the Maori - share a "
             "different emphasis: they create domains in which the "
             "language is not merely remembered but required. Nurseries, "
             "local government, broadcasting and, crucially, adolescent "
             "social life supply reasons to use the language that "
             "sentiment alone cannot. The uncomfortable implication is "
             "that a community must be willing to make the language "
             "slightly inconvenient to avoid, rather than simply admirable "
             "to preserve.",
     "qs": [{"q": "What does the writer say about recording final "
                  "speakers?",
             "opts": ["It is the most effective method available",
                      "It is completely useless",
                      "It preserves material but cannot reverse decline",
                      "It should be made legally compulsory"], "a": 2},
            {"q": "What do the successful programmes have in common?",
             "opts": ["Very large government funding",
                      "Contexts in which the language is necessary",
                      "A focus on elderly speakers",
                      "Detailed written grammar books"], "a": 1}]},
    {"id": 2402, "level": "B2", "secs": 105,
     "text": "Economists have long treated traffic congestion as a problem "
             "of insufficient capacity, and for most of the twentieth "
             "century governments responded accordingly, widening roads "
             "and building bypasses. The persistent failure of these "
             "measures produced one of the more robust findings in "
             "transport research: induced demand. Additional road space "
             "lowers the effective cost of driving, which draws in "
             "journeys that were previously made at other times, by other "
             "routes, by other modes, or not at all, until congestion "
             "returns to roughly its former level. The finding is not "
             "universally accepted as a reason to stop building roads - a "
             "new road may still be justified by the journeys it enables, "
             "even if it does not reduce delay. What it does undermine is "
             "the specific promise that construction will cure congestion, "
             "a promise that continues to appear in political manifestos "
             "with undiminished confidence.",
     "qs": [{"q": "What is \"induced demand\"?",
             "opts": ["Drivers campaigning for more roads",
                      "New road space generating additional traffic",
                      "Congestion falling permanently after construction",
                      "Public transport losing its funding"], "a": 1},
            {"q": "What is the writer's position on building roads?",
             "opts": ["No new roads should ever be built",
                      "Roads may be worthwhile, but not as a cure for "
                      "congestion",
                      "Congestion is not a real problem",
                      "Political manifestos are usually accurate"],
             "a": 1}]},
    {"id": 2403, "level": "B2", "secs": 105,
     "text": "Peer review is routinely described as the mechanism that "
             "guarantees the reliability of published science. It does "
             "nothing of the kind, and was never designed to. A reviewer "
             "sees a manuscript, not a laboratory; they can assess whether "
             "the argument follows from the data presented, but not "
             "whether the data were honestly obtained, competently "
             "measured or selectively reported. Detecting fabrication "
             "requires access that reviewers do not have and time they are "
             "not paid for. This is not an argument for abandoning the "
             "system, which filters out a great deal of incoherent and "
             "unoriginal work. It is an argument against the weight placed "
             "on the phrase \"peer-reviewed\" in public debate, where it "
             "is frequently deployed as though it settled a question that "
             "it can, at best, only narrow.",
     "qs": [{"q": "According to the writer, what can reviewers NOT "
                  "assess?",
             "opts": ["Whether the writing is clear",
                      "Whether the argument follows from the data",
                      "Whether the data are genuine",
                      "Whether the topic is original"], "a": 2},
            {"q": "What is the writer's main point?",
             "opts": ["Peer review should be abolished",
                      "Peer review is given too much authority in public "
                      "debate",
                      "Reviewers should be paid much more",
                      "Fabrication of data is extremely rare"], "a": 1}]},

    # ---------------- C1 ----------------
    {"id": 2501, "level": "C1", "secs": 120,
     "text": "There is a species of argument, common in discussions of "
             "technology, that proceeds by treating an unfinished thing as "
             "though it were finished. Critics of early photography "
             "complained that it could not render colour; enthusiasts "
             "replied that it soon would. Both were addressing a static "
             "object, and both were wrong in the same way, because what "
             "changed was not the fidelity of the image but the social "
             "function of images altogether - who was portrayed, how "
             "often, and on whose authority. The interesting consequences "
             "of a technology are rarely the ones its designers advertise "
             "or its opponents fear, since both parties are obliged to "
             "speak in the vocabulary of the thing being replaced. "
             "Photography was not a better kind of portrait painting; the "
             "automobile was not a faster horse. It follows that confident "
             "predictions about a technology's effects, whether "
             "enthusiastic or alarmed, should be treated as evidence of "
             "what their authors already believed rather than as "
             "forecasts.",
     "qs": [{"q": "What error does the writer attribute to BOTH critics "
                  "and enthusiasts of photography?",
             "opts": ["Both overestimated how fast it would improve",
                      "Both judged it in the terms of what it replaced",
                      "Both ignored the question of colour",
                      "Both were commercially motivated"], "a": 1},
            {"q": "What does the writer conclude about confident "
                  "predictions?",
             "opts": ["They are usually accurate in the long run",
                      "They reveal the prior beliefs of those who make "
                      "them",
                      "They should not be published",
                      "They improve with technical expertise"], "a": 1}]},
    {"id": 2502, "level": "C1", "secs": 120,
     "text": "Legal systems that rely on precedent are frequently praised "
             "for their stability and criticised for their conservatism, "
             "as though these were two descriptions of the same property. "
             "They are not. Precedent constrains the reasoning a judge may "
             "offer, not the outcome a judge may reach; a sufficiently "
             "determined court can distinguish an inconvenient authority "
             "on facts so narrow that the distinction is transparent, and "
             "the doctrine survives intact while the rule quietly changes. "
             "What precedent genuinely supplies is a record of the "
             "arguments a society has been prepared to accept, accumulated "
             "over time and available for inspection. Its value is "
             "therefore archival as much as regulative. The common "
             "complaint that judges \"make law\" misses the point: the "
             "alternative is not judges who merely apply it, but judges "
             "whose lawmaking leaves no trace and can be neither examined "
             "nor overruled.",
     "qs": [{"q": "What distinction does the writer draw about precedent?",
             "opts": ["It constrains outcomes but not reasoning",
                      "It constrains reasoning but not outcomes",
                      "It constrains neither in practice",
                      "It constrains both equally"], "a": 1},
            {"q": "How does the writer respond to the complaint that "
                  "judges \"make law\"?",
             "opts": ["Judges should be prevented from making law",
                      "Judges in fact rarely make law",
                      "Lawmaking that leaves no trace would be worse",
                      "The complaint is entirely accurate"], "a": 2}]},
    {"id": 2503, "level": "C1", "secs": 120,
     "text": "The vocabulary of \"work-life balance\" has proved "
             "remarkably durable despite describing something almost "
             "nobody experiences, and its durability is instructive. A "
             "balance implies two quantities on a single scale, "
             "exchangeable at some rate, with an optimum somewhere in the "
             "middle. Very little about the difficulty is captured by this "
             "image. The problem for most people is not the total quantity "
             "of hours but their predictability and their boundaries: an "
             "hour of work at nine on a Tuesday morning and an hour at "
             "nine on a Sunday evening are not interchangeable units, and "
             "treating them as such is precisely the error that produces "
             "the complaint. Metaphors of this kind are not innocent. "
             "Having accepted the scale, one is committed to negotiating a "
             "position on it, which is why so many workplace policies "
             "concern how much and so few concern when, or who decides.",
     "qs": [{"q": "Why does the writer object to the \"balance\" "
                  "metaphor?",
             "opts": ["It is unnecessarily pessimistic",
                      "It treats hours as interchangeable quantities",
                      "It is used only by employers",
                      "It ignores the question of pay"], "a": 1},
            {"q": "What consequence does the writer identify?",
             "opts": ["Policies address quantity rather than timing and "
                      "control",
                      "Workers end up working fewer hours",
                      "Metaphors are now avoided in policy documents",
                      "Employers have rejected the whole idea"], "a": 0}]},
]

READ_BY_LEVEL = {}
for _r in READ_ITEMS:
    READ_BY_LEVEL.setdefault(_r["level"], []).append(_r)
READ_BY_ID = {r["id"]: r for r in READ_ITEMS}
