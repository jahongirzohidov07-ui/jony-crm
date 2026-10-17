# Student course learning motivation

Applies to English Intensive (192 lessons / 32 weeks) and German B1 (72 lessons / 24 weeks). Speaking scenery is English-only because only English currently has the inline AI partner.

## Learning events

- First correct ordinary exact practice answer: 2 XP, no coin, once per question. Ordinary exercises can also appear in teaching material, so these are not labeled independent mastery.
- Correcting an earlier wrong answer: 2 XP, once per question, no coin.
- Due recall: 8 XP and 1 coin per eligible spaced stage. Immediate retries do not earn rewards.
- Weekly new-context checkpoint: 3 canonical questions; all correct earns 15 XP and 2 coins once. A capped checkpoint reward remains claimable after the daily cap resets. A failed checkpoint can be retried after 7 days as correction practice, not a new independent pass.
- Self-checked writing and speaking receive no automatic mastery rewards.
- Daily target: 5 distinct useful questions. Course rewards are capped across both languages at 20 awards per day. There is no lost streak or penalty for absence.

The existing XP journal and coin ledger remain the source of truth. Learner-scoped database locking, unique reward keys and a single transaction protect concurrent requests. No schema migration or production seed is required.

## Review and cooperation

Review prioritizes unresolved wrong answers, then due recall, in a finite daily queue of at most 5. Lesson selection is preserved independently of answer submissions.

Weekly cooperation is opt-in, same language and stage, with stable groups of at most 20. Only masked aliases are shared. Test branches, demo accounts and inactive students cannot enter real cohorts. Leaderboard output is limited to the top three, with personal and cooperative progress rather than exposing a bottom ranking. A student can leave; rejoining does not create a new identity or cohort.

## Meaning of counts

Lesson completion means all answers were submitted, not certified mastery. Rewarded learning actions distinguish independent correctness, correction and spaced recall. Course targets do not guarantee a B1/B2 certificate. The platform cannot prove that a learner did not consult external help.

## Validation

Run the student identity, course practice, course motivation, checkpoint-data and theme tests, TypeScript check and Vite build. Browser checks should use the isolated local fixture for writes; production verification must avoid adding artificial progress or rewards to real students.
