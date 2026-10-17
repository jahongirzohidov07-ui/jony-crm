# Course learning evidence and creative portfolio

## Behaviour

- Lesson practice readiness requires at least three distinct latest-correct exact questions (or all when fewer exist), spanning at least two available sections. Durable retention additionally requires a correct review at least 24 hours after initial success, after the most recent failure. Passed checkpoints and earned rewards remain historical records.
- Daily effort counts distinct meaningful canonical questions attempted in the learner's Tashkent day, independently of XP caps, disabled reward rules or demo status. Open answers count effort, never verified mastery. Duplicate questions do not inflate the day.
- Each language has a stable current-day, approximately 15-minute plan of three targeted actions. Completed steps survive reload; an exposed/unavailable recall becomes ordinary practice, not an impossible task or a falsely verified recall. The plan estimates time, it does not measure time on task.
- The home page no longer requests saved answer detail automatically. Course detail loads only after explicitly opening a lesson, preserving unexposed recall questions.
- Evidence separates first attempts, latest delayed review, readiness, retention and skill counts. Same-question before/after comparison uses only the identical reviewed question set. No CEFR, speaking-quality or learning-gain claim is inferred from XP or text length.
- Private portfolios support dialogue, story or speaking works, immutable versions and side-by-side text/audio comparison. Each lesson allows eight works, each with three versions. Recording is optional (60 seconds / 1 MiB per recording); each learner has total 8 MiB audio and 2 MiB text limits. Nothing is automatically discarded. Delete requires the learner's confirmation.
- Optimistic compare-and-swap rejects stale portfolio writes; validation rejects oversized/unsupported audio, wrong learner/language/lesson access and anonymous requests. No migration, public media URL or additional XP writer is introduced.

## Verification

Isolated SQLite backend suites cover existing course/reward behaviour, new readiness/retention and effort, stable plans, day/language/user boundaries, immutable versions, quotas and validation. TypeScript and Vite production builds checked. Browser QA uses an isolated local learner and the actual components/backend: targeted plan navigation, a correct recall and updated totals, creating and revising a portfolio, unchanged earlier version after reload, and English/German separation. At 360 x 800, document width remained within viewport.

Existing Android native bridge regression tests remain in CI. This change was checked in a narrow browser viewport; that is not a new Android instrumented run. Actual microphone capture/playback and hardware permission variations need physical-device verification. No production learner records were modified by QA.

Graphify update was attempted in the worktree; the local graph/runner setup could not complete an update. No graph freshness claim is made.
