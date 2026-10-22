# Student ranking and reward guidance

- Rank membership uses a valid integer rank 1 through 10, never the absence of a positive gap. Equal XP sorts by student ID consistently for ranking and weekly winner selection. No top-ten coin promise; weekly coin belongs to the overall winner under existing rules.
- Badges describe recorded activity: vocabulary correct-answer count is not unique known words, and 500 XP is not completion of a language level. Existing reward thresholds remain unchanged.
- Shop reward selection persists on this device per student ID. It never submits a purchase. Available balance excludes held coins. Sold-out goals remain visible; removed goals explain the fallback.
- Read-only own-student reward-path shows current earning rules and real destinations, not an invented daily coin conversion. Only ledger-backed entries say awarded. Eligibility, untracked payment and staff-discretion rewards are distinct; absence of a request never means pending approval.
- Streak reward status uses its current run and ledger reference. League promotions without reliable payment references direct the learner to coin history. Wordbank earning steps only appear when enabled and ready.

Validation: focused rendering/helper tests, backend isolation/read-only/status regressions, TypeScript, lint/build, and isolated Android MainActivity/WebView scenarios. Actual final test results are recorded in the pull request. This is not a physical-device or Play Store release.
