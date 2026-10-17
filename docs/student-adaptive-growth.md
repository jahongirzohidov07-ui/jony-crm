# Student adaptive growth — 2026-10-18

## Behavior

- Learners select a language-scoped 5/15/25-minute estimated plan. Stable targets preserve completed work when duration changes. Before the first daily effort, the explicit choice updates the reporting denominator; afterward it stays fixed. Older three-target plans expand safely without resetting IDs or progress.
- Repeated mistakes select a concrete supporting question in the same section or an earlier lesson when tomorrow's plan is made; current-day targets remain stable. Unseen questions stay within the learner's current lesson range. Foreground/resume and Tashkent day rollover refresh the plan.
- Weekly cooperation counts distinct substantive question/day attempts after joining, including wrong attempts that earn no XP. Existing privacy, opt-in, cohort capacity and daily/weekly caps remain. Canonical short English foundation speaking answers qualify; arbitrary rating clicks do not. A teacher-mediated discussion prompt accompanies the common goal.
- Learners may choose lesson-grounded real-life missions when creating private portfolio work. The mission remains attached across immutable revisions. Each saved revision carries an observable text-pattern observation, one next improvement and a retry action. Audio content is not assessed; suggestions do not award mastery or XP. After three revisions, retry creates a separate work rather than rewriting history.
- The personal 28-day report separates activity days, completed plan days, mature day-seven return, same-question recall after at least seven days, and speaking practice volume. Missing evidence remains unknown. It is not an aggregate experiment, a CEFR evaluation or proof of causal learning improvement.

## Validation

- 94 backend tests: course practice 19, motivation 27, learning evidence 19, plan/measurement 16, portfolio 13.
- 11 student state/API regressions and 8 native bridge regressions.
- TypeScript and production Vite build pass. Existing large-bundle warnings remain.
- Android AdaptiveLearningTest: 4/4 pass in 107.312 seconds (budget persistence/language isolation, wrong-answer team effort without XP inflation, honest measurement, mission/coaching immutable revisions).
- Android LearningEvidenceTest: 7/7 pass in 131.777 seconds, including actual silent MediaRecorder capture, persistence, reload and playback decoding.

Android 15 / API35, WebView124.0.6367.219, 720x1600 at320dpi. Tests use the genuine MainActivity/WebView/native bridge in an isolated .qa APK with real React and backend business logic, in-memory learner database and deterministic speaking-AI reply. UI mutations use native taps/keyboard and visible controls. No production learners were modified. The Play Store installation flow, physical microphone quality, real AI quality and all vendor devices are outside this test.

Tools, instrumentation sources, logs and screenshots are retained under C:/Users/Acer/AppData/Local/JonyAndroidQA. New suite: adaptive-instrumentation-1.log and adaptive-evidence/. Regression log: adaptive-regression.log. Fixtures are in the worktree's ignored _inbox/. New backend tests are included in CI.

Graphify update was attempted; the installed launcher references a missing local runner. Graph freshness is not asserted.
