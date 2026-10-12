import { Fragment, lazy, type ReactNode } from "react";
import { useParams } from "react-router-dom";
import { useLearningLanguage } from "../lib/lang";

const StudentRussianCourse = lazy(() => import("../pages/student/StudentRussianCourse"));

/** Select the course before mounting legacy exercise loaders. */
export function StudentLanguageRoute({children, section = "vocabulary"}: {
  children: ReactNode; section?: string;
}) {
  const language = useLearningLanguage();
  const { skill } = useParams();
  if (language === "ru") {
    return <StudentRussianCourse key={skill || section} initialSection={skill || section} />;
  }
  return <Fragment key={language}>{children}</Fragment>;
}
export { StudentRussianCourse };
