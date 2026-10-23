type PracticeSource = { id: string; status: string };
export type RewardPracticePlan =
  | { kind: "link"; href: string; label: string }
  | { kind: "vocab"; sourceId: string; language: string; label: string }
  | { kind: "unavailable"; message: string }
  | null;

export function rewardPracticePlan(source: PracticeSource, language = "en"): RewardPracticePlan {
  if (source.status !== "in_progress" && source.status !== "eligible") return null;
  const family = source.id.split(":")[0];
  if (!["league", "streak", "wordbank", "daily-six"].includes(family) || !source.id.split(":")[1]) {
    return { kind: "unavailable", message: "Bu shart uchun to‘g‘ridan-to‘g‘ri mashq hozir mavjud emas." };
  }
  const query = new URLSearchParams({ reward_source: source.id });
  if (family === "daily-six") {
    return language === "en" || language === "de"
      ? { kind: "link", href: `/student/course-practice?view=daily-six&${query}`, label: "Kunlik 6 qadamni davom ettirish" }
      : { kind: "unavailable", message: "Kunlik 6 qadam ingliz va nemis tillarida mavjud." };
  }
  if (family === "wordbank") {
    return language === "en"
      ? { kind: "link", href: `/student/words/practice?${query}`, label: "Moslashtirilgan so‘z mashqini boshlash" }
      : { kind: "unavailable", message: "So‘z bilish mashqi faqat ingliz tilida mavjud." };
  }
  if (family === "league" && (language === "en" || language === "de")) {
    return { kind: "link", href: `/student/course-practice?view=session&${query}`, label: "Bugungi XP mashqini boshlash" };
  }
  // StudentLanguageRoute replaces Russian legacy games with a course overview.
  // Do not present that overview as a concrete exercise or change the user's language.
  if (language === "ru") {
    return { kind: "unavailable", message: "Rus tilida bu mukofot uchun to‘g‘ridan-to‘g‘ri lug‘at mashqi hozir mavjud emas." };
  }
  if (!["en", "de", "ko"].includes(language)) {
    return { kind: "unavailable", message: "Tanlangan tilda bu mashq hozir mavjud emas." };
  }
  return { kind: "vocab", sourceId: source.id, language, label: "Lug‘at mashqini boshlash" };
}

export type RewardVocabUnit = {
  key: string; n: number; percent: number; learned3: number; learned6: number; passed: boolean;
};
export type RewardVocabUnits = { language: string; units: RewardVocabUnit[] };

export async function rewardVocabHref(
  source: PracticeSource,
  language: string,
  load: (path: string) => Promise<RewardVocabUnits>,
): Promise<string> {
  const plan = rewardPracticePlan(source, language);
  if (plan?.kind !== "vocab") throw new Error("Bu shart uchun lug‘at mashqi mavjud emas.");
  const response = await load(`/student/vocab/units?language=${encodeURIComponent(language)}`);
  if (response.language !== language || !Array.isArray(response.units)) {
    throw new Error("Lug‘at bo‘limlarini tekshirib bo‘lmadi. Qayta urinib ko‘ring.");
  }
  // The choice game requires at least four words; count=10 requests up to ten.
  const units = response.units.filter(u => typeof u.key === "string" && u.key.length > 0 &&
    Number.isFinite(u.n) && u.n >= 4);
  const unit = units.find(u => !u.passed && u.learned6 < u.n &&
    (u.percent > 0 || u.learned3 > 0 || u.learned6 > 0)) ?? units.find(u => !u.passed && u.learned6 < u.n) ?? units[0];
  if (!unit) throw new Error("Mashq uchun yetarli so‘zli bo‘lim topilmadi. Keyinroq qayta urinib ko‘ring.");
  const query = new URLSearchParams({ lang: language, count: "10", reward_source: source.id });
  // The API also uses Boshqa for NULL topics; it cannot be targeted as a literal unit.
  // In that case launch the actual mixed game, never an invented unit or a list page.
  if (unit.key !== "Boshqa") query.set("unit", unit.key);
  return `/student/games/en_uz?${query}`;
}
