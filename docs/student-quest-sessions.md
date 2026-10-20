# Student focused sessions — 2026-10-20

## Behavior

Daily-plan entry opens `view=session`, rendering only the first unfinished server plan step. A saved answer stays on screen for feedback; explicit Next reloads authoritative progress. Reading text and lesson audio stay with the relevant question. English speaking retains the real existing flow; German uses its canonical question. Finished plans display a stopping point, without declaring all answers correct or increasing rewards locally.

The complete lesson remains accessible separately. Session completion invalidates the exact parent answer cache, including saves returning after navigation. UI advancement is mounted-only. Tashkent day changes reload the plan and clear session drafts; submissions check the day too. Unsaved drafts do not persist across full page reloads.

Question controls use public prompt/options only. Unambiguous choices become accessible radio cards, explicit letter-sequence tasks use order cards, and supported sentence ordering uses word cards. Free text remains available. Multiple-answer or ambiguous questions remain writing tasks. Answer keys are never used by interaction selection.

Home and Learn foreground the course goal and daily plan. XP, coins, activity levels and leagues remain available in expandable details. Actual first-attempt results are labelled as question evidence, never CEFR/mastery. Current lesson objectives derive from canonical course sections. Other-language fallbacks remain.

## Verification

Core regression checks: personal plan/measurement 16 passed; student regressions 11 passed; native speech bridge 8 passed; focused-time assertions passed. Question-control tests: 16 passed. Audit of 14,880 canonical questions found 2,324 compatible choice inputs and 20 compatible word-order inputs, with zero incompatible conversions. TypeScript project build, targeted lint and production Vite build passed. Final Android results are recorded below. Real user engagement and learning outcomes are not established by these tests.

Graphify update was attempted in the worktree and failed with process exit -1073741819 and no diagnostics.
