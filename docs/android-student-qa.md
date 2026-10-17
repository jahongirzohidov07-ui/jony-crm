# Android Student gamification QA — 2026-10-17

## Environment and scope

Android 15 / API 35 Google APIs x86_64 emulator, Windows WHPX, 720 x 1600 at 320 dpi (360 CSS px); Android WebView 124.0.6367.219. Student Android source at production commit `18958ea1f40c23a528c14c4d376de8669e90dd57` was exported into a disposable `.qa` application, with the genuine MainActivity, native bridge and WebView. It loaded the actual React course components and actual course backend using an isolated in-memory SQLite learner. No production student or reward data was changed.

Debug-only differences: local origin allowlist, no notification worker, cleartext permitted for the loopback fixture, upload signing omitted, and screenshot restriction omitted only in this test copy. No Android Java/manifest changes are shipped by this patch. Speaking AI replies were deterministic in the fixture; acoustic recognition, microphone permission dialogs, real AI quality, Play Store binary equivalence, other OS/WebView versions and device-vendor variations were not verified.

## Results

The final AndroidJUnitRunner run passed **6/6** tests in **77.068 seconds**. Inputs were entered using real native taps and Android key events after focusing the actual DOM input. Reward writes went through visible React controls, not direct API seeding during assertions.

1. Ordinary correct practice awards 2 XP once; immediate repeat gives no further XP; reload retains the result and total.
2. Week 1 journey opens its new-question checkpoint, all 3 answers award 15 XP / 2 coins, the passed checkpoint cannot resubmit, and navigation returns focus to the lesson.
3. Football / robots / daily-life speaking scenery switches correctly; conversation resets; a robot description saves without unverified mastery rewards; the Android speech adapter exists.
4. Weekly cohort join and leave persist across reload; the isolated participant is anonymous and no real student name appears.
5. Five due recalls each award 8 XP / 1 coin once, disappear from today's queue, complete the finite daily goal, and retain totals on reload.
6. German shows 6 months / 72 lessons, English shows 192 lessons, German reward/cohort state remains separate, and the German journey does not overflow the phone viewport horizontally.

Test setup failures (launcher resolution, synthetic input focus, and previously exposed review fixtures) were corrected in the disposable harness before the final passing run; they were not reported as production defects.

## Shipped corrections

- A thrown native recognition start/stop now releases its session and emits completion, allowing retry.
- Abort detaches old recognition callbacks before native stop; late final results cannot revive a cancelled session. Normal stop still accepts a final transcript.
- TTS cancellation invalidates both active and queued callbacks; native errors and reentrant replacements do not leave the speech queue busy.
- Course speaking now displays a recoverable message when text-to-speech fails instead of silently doing nothing.

Eight transport-level regression tests pass via `node scripts/test-native-bridge.cjs`; CI runs them. TypeScript and Vite production build also pass. These mock-transport tests supplement, and do not replace, the six native Android tests.

## Evidence and installed tools

The emulator/SDK/JDK/Gradle installation and complete disposable Android test project are retained at `C:\Users\Acer\AppData\Local\JonyAndroidQA`. The final runner log is `instrumentation-final.log`; per-test screenshots, DOM and PASS results are under `evidence-passed/`. A review copy is under this checkout's ignored `_inbox/android-qa-evidence/` directory. The test fixture lives in the existing intensive-release checkout's `_inbox/motivation_qa.py` and `_inbox/student-course-qa/`.

The repository graph refresh was attempted, but the installed graphify executable failed because its local runner file was missing. No graph freshness claim is made.
