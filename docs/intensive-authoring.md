# Intensive content maintenance

The application and print books share authored data. Do not pad missing lessons with repeated passages or duplicate headwords.

## Sources

- `src/data/intensive-grammar-map.json`: 27 modules, 411 separate grammar topics.
- The first 500 entries in `src/data/intensive-vocabulary.json` are the foundation source. Subsequent entries are assembled from `src/data/intensive/words-month2.json` through `words-month8.json` (500 each).
- `src/data/intensive/grammar-*.json`: two authored questions per topic, in addition to the map-model reconstruction.
- `src/data/intensive/skills-*.json`: one distinct reading and listening passage per lesson, answer keys, production tasks, models and teacher notes.
- `src/data/intensive-month-outcomes.json`: internal monthly learning targets.

Edit the source pack, then rebuild the combined files; otherwise the next assembly will replace changes made only to a combined output. Keep British IPA, Uzbek Latin translations and natural target-word usage in examples. Earlier months have priority when resolving duplicate headwords. An inflection is not a new lexical entry merely to increase the count.

## Build and validate

1. `node scripts/assemble-intensive.cjs` — refuses missing IDs, duplicate words, incomplete packs or repeated passages.
2. `node scripts/test-intensive.cjs --export` — checks the full lesson allocation and exercise data, writes the shared print export.
3. `python scripts/build-intensive-pdfs.py` — teacher guide, full/monthly vocabulary and grammar/vocabulary workbooks.
4. `python scripts/build-intensive-skills-pdfs.py` — eight monthly skill books. `--months 1` rebuilds one month.
5. Run the TypeScript/application build and inspect representative PDF pages, including long final-month texts and the answer section.

PDF scripts use ReportLab and Windows Arial fonts. Logo and pattern come from the existing Jony brand assets. The intermediate `public/intensive/course-export.json` is not a deployment artifact.

## Answer and level checks

Automatic tests establish structural completeness, not independent pedagogical accreditation. Review meanings, IPA, passage evidence, plausible answer alternatives and writing-model lengths before publishing. Case-sensitive exercises explicitly set `caseSensitive: true`; ordinary answers ignore case and basic punctuation. Use constrained choices when punctuation alone is the learning objective.

Quiz scores are session practice, not stored official grades. The production rubric is an internal 0–8 feedback scale, not a Multilevel conversion. Browser speech uses the device's synthetic English voice; teachers can read the provided script when a voice is unavailable.

The 32 teaching weeks contain 192 lessons; remaining calendar days within eight months accommodate holidays and catch-up. Weeks 28–32 revisit grammar: diagnose with up to 20 questions, reteach the 3–5 weakest topics rather than every card. Vocabulary continues through all 4,000 slots.

Writing-format reference checked 2026-10-05: https://gov.uz/oz/uzbmb/sections/view/49531 and the linked current task specification. The course supplies original classroom practice, not official exam papers or a guaranteed certificate result.
