# Intensive final-month exam preparation

Verified on 2026-10-07. Scope: one standalone component, plus this review. No existing page/library modifications, commit, or deployment.

## Parent integration

Import the default export from `src/components/IntensiveExamPreparation.tsx` and render it in month 8. Pass `storageKey` containing the current learner/group identifier, and `canReview` from the application's existing teacher permission. The component adds no authentication and makes no application API calls.

Example parent usage (integration is intentionally left to the parent owner):

```tsx
<IntensiveExamPreparation
  storageKey={`jony:intensive:exam:v1:${learnerId}:${groupId}`}
  canReview={existingTeacherPermission}
/>
```

Both props are optional. `canReview` defaults to false. Without a key, the component uses a visibly local, shared-browser practice notebook. Identity changes remount internal state. `canReview` only controls the local UI; it is not a security boundary or verified teacher identity. Persisted data is editable through browser tools. Do not import these marks into official grades without a separate trusted review process.

## Verified official sources

The user's requested `uzbmb.gov.uz` host was unavailable. The current government portal explicitly links the agency's actual `uzbmb.uz` host; all agency asset URLs below were discovered from official pages, not guessed.

| Source | Verification and use |
| --- | --- |
| [Government test format](https://gov.uz/oz/uzbmb/sections/view/49512) | Current Multilevel subsection: Listening 45 minutes / 6 parts / 35 questions; Reading 60 minutes / 5 parts / 35 questions; Writing 60 minutes / 2 parts / 3 responses. Other sections on this page describe separate single-level exams and must not be mixed into Multilevel. |
| [Government sample index](https://gov.uz/oz/uzbmb/sections/view/49518) | Page shows last update 2026-09-03. Direct links to English Multilevel ZIP and new-format writing archive verified. |
| [Official English sample ZIP](https://uzbmb.uz/upload/file/chet_tili/test_namuna/Ingliz_Multi_V1.zip) | Downloaded into memory and enumerated successfully: `LISTENING PAPER.pdf` (862,114 bytes), `listening.mp3` (61,912,084 bytes), `READING PAPER.pdf` (1,074,539 bytes), `WRITING PAPER.pdf` (352,182 bytes), `Answer key.pdf` (241,910 bytes). Link supplies the official recorded listening material, not browser TTS. No standalone MP3 URL is invented. Archive audio was not acoustically audited. |
| [New writing sample RAR](https://api-portal.gov.uz/uploads/165/2025/10/13/5a2f6c1e-345c-2d5c-bee2-ad0d7765e2c0_media_.rar) | Downloaded and enumerated; English, German, French, Arabic and Turkish PDFs exist. Extracted/read `INGLIZ TILI.pdf`: fitness-club email tasks and a city/town discussion task, plus sample responses with examiner comments. Use its task page during practice; keep sample responses for review. |
| [New writing specification](https://api-portal.gov.uz/uploads/165/2025/10/13/99dfbb36-0f1d-2c70-8a4e-e1382a5f255b_media_.pdf) | Read all six pages: about 50-word informal email, 120–150-word formal email, 180–200-word online text; 60 minutes total. Recommended 25/35-minute split, not mandatory separate deadlines. Raw task maxima 5/5/6. |
| [New writing criteria](https://api-portal.gov.uz/uploads/165/2025/10/13/b260e792-2fc6-630d-5bfe-399a2a0e55b6_media_.pdf) | Read the official rubric; linked for human marking. The component records individual teacher marks and comments, without calculating a standardized score or CEFR level. |
| [Government criteria index](https://gov.uz/oz/uzbmb/sections/view/49531) | Page shows last update 2026-01-26. Verified links to new writing specification/rubric and speaking format/rubrics. |
| [Speaking format and English samples](https://uzbmb.uz/upload/file/pdf/phone/Speaking_yangi_format.pdf) | Downloaded successfully and extracted/read PDF text. Part 1.1: three 30-second answers; 1.2: 45/30/30 seconds with two pictures; Part 2: 60-second preparation, 120-second answer covering three questions, no picture description required; Part 3: 60-second preparation, 120-second balanced argument. Official pictures remain in the linked PDF. |
| [British Council B2 business interview](https://learnenglish.britishcouncil.org/free-resources/listening/b2/business-interview) | Opened public lesson containing recorded listening, activities and transcript. Supplemental B2 work only; never counted as an official Multilevel paper. |

The older agency general-format page still describes the older writing tasks. The government format page and newer specification take precedence. The old writing paper inside the English ZIP is explicitly superseded in the module by the newer English writing sample. The sample ZIP remains suitable as the linked official source for the listening/reading practice workflow; no claim is made that it is a newly issued 2026 test.

## Implemented behavior

- Four-week preparation/review plan; clear official-format overview and resource checklist.
- Sequential Listening → Reading → Writing → Speaking workflow. Each section starts explicitly; only one section can run. No pause and no restarting the same section to gain time.
- Absolute start/deadline timestamps persist immediately to local storage. Reloading or switching tabs does not reset a deadline. Expired sections stop accepting input, including events occurring between timer ticks. Early submission closes that section.
- Speaking automatically advances through the ten answer/preparation stages. Its 9:15 total is explicitly the sum of task timers, excluding instructions and technical time; it is not presented as official appointment duration.
- 35 numbered listening answers, 35 reading answers, three writing responses with approximate word counts, and an external speaking-recording/live-observation note.
- Teacher controls are opt-in via parent permission, and enabled only after all four sections finish. Require teacher name, all five raw marks, and feedback for each skill. Editing a review invalidates its previous confirmation.
- Speaking uses qualitative teacher feedback against the linked rubric. No invented overall numeric score, CEFR conversion, pass prediction, or automatic grading.
- JSON export includes responses, timestamps, review, source URLs, and `notOfficialScore: true`. Explicit reset confirmation prevents accidental replacement. Malformed saved state is not automatically overwritten. Storage failures are visible.

## Limits

- The page is a companion to externally opened official papers/audio, not a hosted full-test bank. No short authored passages are labelled full mocks. No copyrighted sample paper/audio is copied into the repository.
- ZIP/RAR extraction and an external audio player are needed. The official package can be large. Test playback before starting. The browser search fetcher returned 502 for agency assets, but direct public downloads succeeded; government index links are included as fallbacks.
- The written 165-minute practice is section-based. Manual starts between sections allow breaks; the UI explicitly instructs immediate continuation for a realistic written simulation. It is not a proctored continuous exam.
- Speaking requires a teacher or separate recorder and the official PDF. No microphone capture, audio upload, remote submission, or server sync.
- Practice storage is device-local, with no cross-tab conflict resolution or cross-device transfer/import. Use one active tab per learner and export before clearing browser data. The parent should pass a learner-specific storage key. Local clock changes can affect timing; this is practice, not an anti-cheating system.
- Only one current attempt per storage key is retained. Export before starting another attempt. No UI integration was made within this restricted scope.

## Validation

- Standalone TypeScript check passed with strict mode, unused-local/parameter checks, React JSX, bundler resolution and ES2023/DOM libraries.
- Component-targeted oxlint completed successfully.
- In-memory behavioral assertions passed: persisted answer/timestamp round-trip; reload-safe remaining time; deadline expiry; early submission; speaking-stage boundaries; integer score bounds including valid zero; corrupt/incorrect-version saved-state rejection; standalone React rendering; reviewer controls hidden by default.
- No full application build or existing-file tests were changed. Browser interaction and parent integration need validation by the integrating owner.
- Required `graphify query` was attempted before source inspection; required `graphify update .` was attempted after code changes. Both failed with `uv trampoline failed to canonicalize script path`; the graph could not be refreshed.
