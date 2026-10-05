# Jony Deutsch — course scope

Requested target: zero to Goethe-Zertifikat B1 in six months. The timetable uses 24 teaching weeks, with three 120-minute main lessons and three linked 60-minute support sessions per week (216 contact hours). Independent work is planned for 75 minutes on six days per week. Calendar holidays are handled by the group's timetable, not invented in this course map.

## Structure

- Weeks 1–8: A1 foundation and everyday interaction.
- Weeks 9–16: A2, past experiences and more independent interaction.
- Weeks 17–24: B1, opinions, connected speech, writing and exam preparation.
- 100 original vocabulary entries per week, divided 33/33/34 across the three main lessons. Support uses only already assigned entries.
- German nouns include articles and plural information; verbs include key forms where applicable. Entries carry IPA, Uzbek meaning, a German example and its Uzbek translation.
- Grammar topics have separate form-focused exercises. Free speaking/writing is teacher assessed; automatic short-answer checks are practice, not official scores.
- Each main lesson has its own reading, listening script, speaking and writing tasks. Listening uses a teacher reading or a device-provided German synthetic voice, explicitly labelled in the UI.
- Local monthly mastery target (80% in short-answer grammar/vocabulary practice) is distinct from Goethe assessment. Remedial support and reassessment follow low results. Completing the calendar is not evidence of certificate readiness.

## Official references

Checked 2026-10-05:

- https://www.goethe.de/ins/de/de/m/prf/prf/gzb1/inf.html — modules and timings. Goethe describes 350–650 teaching units of 45 minutes depending on prior knowledge and learning conditions. Our contact schedule is 288 such units, so independent work and readiness checks are essential; no six-month pass guarantee is made.
- https://www.goethe.de/ins/dk/de/spr/prf/ueb/pb1.html — official adult/youth model tests and audio; use the relevant candidate version for full timed simulations.
- https://www.goethe.de/pro/relaunch/prf/bg/Goethe-Zertifikat_B1_Wortliste.pdf — scope reference (approximately 2,400 lexical units). Our independently authored teaching vocabulary is not presented as a licensed reproduction or a verified one-to-one copy of this list.

Do not label short internal practice sets as full official Goethe mock exams. Do not relabel synthetic speech as a recorded human listening test.

## Updating

Course data lives in `src/data/german`. The UI reads those same JSON files. Run `node scripts/test-german.cjs` after content changes, then `scripts/build-german-pdfs.py` with Python/reportlab to rebuild printable books. Static course assets are excluded from Python serverless function bundles in `vercel.json`.
