# Russian course in Jony Student

Selecting Russian routes vocabulary, grammar, legacy game links and four skill entry points to the one-year Russian course. Other learning languages retain their existing flows. Language changes publish an event; open pages and browser tabs react to the selection. The home page replaces English-level and daily XP mission cards with a Russian course entry.

The student course uses the exact 144 lessons / 12 months in `src/data/russian/part-1.json` through `part-4.json`. Build exports a server-readable snapshot under `api/`; update source lessons, then regenerate the snapshot when editing curriculum. Vocabulary consists of 1,152 phrase slots, including reviews, not 1,152 unique words.

Vocabulary and grammar practice results are checked on the server and stored per signed-in student, lesson and exercise kind. These are independent practice scores, not an official language level, teacher grade, XP or coin reward. Dialogue comprehension, writing and speaking are self-practice; model answers are for comparison. Listening uses an available Russian device voice and reports when no such voice is installed.

Teacher-issued assignments remain available under Lessons. The generic Intensive lesson/missed-lesson previews are hidden for Russian to avoid displaying English curriculum. Course practice does not submit a teacher assignment automatically.
