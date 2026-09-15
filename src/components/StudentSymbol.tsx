import { UserRound, UsersRound, CalendarDays, GraduationCap, School, MapPin, ShieldCheck, LockKeyhole, Sun, Heart, Bike, Utensils, Plane, PawPrint, MessagesSquare } from "lucide-react";

const symbols = { user: UserRound, family: UsersRound, calendar: CalendarDays, study: GraduationCap, school: School, location: MapPin, shield: ShieldCheck, lock: LockKeyhole, day: Sun, heart: Heart, hobbies: Bike, food: Utensils, travel: Plane, animals: PawPrint, chat: MessagesSquare };
export type StudentSymbolName = keyof typeof symbols;
export function StudentSymbol({ name, tone = "blue" }: { name: StudentSymbolName; tone?: "blue" | "violet" | "amber" | "green" }) {
  const Icon = symbols[name];
  return <span className={`student-symbol student-symbol-${tone}`} aria-hidden="true"><Icon size={21} strokeWidth={2} /></span>;
}
