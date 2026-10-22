export const REWARD_PRACTICE_UPDATED = "jony:reward-practice-updated";
const ANSWER_PATHS = new Set([
  "/student/vocab/answer", "/wordbank/answer",
  "/student/course-practice/answer", "/student/course-practice/motivation/review",
  "/student/course-practice/motivation/challenge", "/student/course-practice/motivation/claim",
  "/student/course-practice/speaking",
]);
export function isRewardPracticeWrite(path: string): boolean {
  return ANSWER_PATHS.has(path.split("?")[0]);
}
export function notifyRewardPracticeWrite(path: string) {
  // A UI refresh must never turn an already saved answer into an apparent failure.
  try {
    if (isRewardPracticeWrite(path) && typeof window !== "undefined" && typeof window.dispatchEvent === "function")
      window.dispatchEvent(new Event(REWARD_PRACTICE_UPDATED));
  } catch { /* answer is already saved; the context also has manual refresh */ }
}
