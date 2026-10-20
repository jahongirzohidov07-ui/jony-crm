import { useId } from 'react';
import { changeCourseQuestionOrder, changeCourseWordOrder, getCourseQuestionChoices, getCourseQuestionOrdering, getCourseWordOrder, parseCourseQuestionOrder, parseCourseWordOrder, selectedCourseChoice } from '../lib/courseQuestionInteraction';
import type { CourseInteractionQuestion } from '../lib/courseQuestionInteraction';

export type CourseQuestionInputProps = {
  question: CourseInteractionQuestion;
  value: string;
  onChange: (value: string) => void;
  disabled?: boolean;
  'aria-label'?: string;
};

export default function CourseQuestionInput({ question, value, onChange, disabled = false, 'aria-label': ariaLabel }: CourseQuestionInputProps) {
  const id = useId();
  const choices = getCourseQuestionChoices(question);
  const selected = selectedCourseChoice(choices, value);
  const words = getCourseWordOrder(question);
  const ordering = words.length ? words : getCourseQuestionOrdering(question);
  const order = words.length ? parseCourseWordOrder(ordering, value) : parseCourseQuestionOrder(ordering, value);
  const changeOrder = words.length ? changeCourseWordOrder : changeCourseQuestionOrder;
  const interactive = choices.length > 0 || ordering.length > 0;
  return <div className="space-y-3">
    {ordering.length > 0 && <fieldset disabled={disabled} aria-describedby={`${id}-help`} className="min-w-0">
      <legend className="mb-2 text-sm font-semibold text-slate-700">
        <span className="sr-only">{question.prompt}. </span>Variantlarni ketma-ket tanlang
      </legend>
      <div className="grid gap-2 sm:grid-cols-2">
        {ordering.map(choice => {
          const position = order.indexOf(choice.value);
          return <button
            key={choice.value}
            type="button"
            disabled={disabled}
            aria-pressed={position >= 0}
            aria-label={`${choice.label}${position >= 0 ? `, ${position + 1}-o‘rinda. Olib tashlash` : '. Tartibga qo‘shish'}`}
            onClick={() => { if (!disabled) onChange(changeOrder(ordering, value, { type: 'toggle', value: choice.value })); }}
            className={`min-h-14 rounded-xl border-2 p-4 text-left text-base focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-600 disabled:opacity-60 ${position >= 0 ? 'border-blue-600 bg-blue-50 text-blue-950' : 'border-slate-200 bg-white text-slate-800'}`}
          >
            {position >= 0 && <span className="mr-2 font-bold">{position + 1}.</span>}
            {choice.label}
          </button>;
        })}
      </div>
      <p role="status" aria-live="polite" className="mt-2 text-sm text-slate-700">
        Tanlangan tartib: {order.length ? (words.length ? order.map(tokenId => words.find(word => word.value === tokenId)!.label).join(' ') : order.join(', ')) : 'Hali tanlanmagan'}
      </p>
      <div className="mt-2 flex flex-wrap gap-2">
        <button type="button" disabled={disabled || !order.length} onClick={() => { if (!disabled && order.length) onChange(changeOrder(ordering, value, { type: 'undo' })); }} className="min-h-11 rounded-xl border border-slate-300 px-4 text-sm focus-visible:outline-2 focus-visible:outline-blue-600 disabled:opacity-50">Oxirgisini bekor qilish</button>
        <button type="button" disabled={disabled || !value} onClick={() => { if (!disabled && value) onChange(''); }} className="min-h-11 rounded-xl border border-slate-300 px-4 text-sm focus-visible:outline-2 focus-visible:outline-blue-600 disabled:opacity-50">Tozalash</button>
      </div>
    </fieldset>}
    {choices.length > 0 && <fieldset disabled={disabled} aria-describedby={`${id}-help`} className="min-w-0">
      <legend className="mb-2 text-sm font-semibold text-slate-700">
        <span className="sr-only">{question.prompt}. </span>Bitta variantni tanlang
      </legend>
      <div className="grid gap-2 sm:grid-cols-2">
        {choices.map((choice, index) => <label key={choice.value} className={`flex min-h-14 cursor-pointer items-center gap-3 rounded-xl border-2 p-4 text-base focus-within:ring-2 focus-within:ring-blue-600 focus-within:ring-offset-2 ${selected === index ? 'border-blue-600 bg-blue-50 text-blue-950' : 'border-slate-200 bg-white text-slate-800'} ${disabled ? 'cursor-not-allowed opacity-60' : 'hover:border-blue-400'}`}>
          <input
            type="radio"
            name={`${id}-${question.id}`}
            value={choice.value}
            checked={selected === index}
            disabled={disabled}
            onChange={() => { if (!disabled) onChange(choice.value); }}
            className="h-5 w-5 shrink-0 accent-blue-600"
          />
          <span className="break-words">{choice.label}</span>
        </label>)}
      </div>
    </fieldset>}
    <div>
      <label htmlFor={`${id}-answer`} className="mb-1 block text-sm font-semibold text-slate-700">
        <span className="sr-only">{question.prompt}. </span>Javobingiz
      </label>
      <textarea
        id={`${id}-answer`}
        value={value}
        maxLength={6000}
        disabled={disabled}
        aria-label={ariaLabel}
        onChange={event => { if (!disabled) onChange(event.target.value); }}
        aria-describedby={interactive ? `${id}-help` : undefined}
        rows={question.mode === 'self' ? 5 : 3}
        placeholder="Javobingizni yozing…"
        className="min-h-24 w-full rounded-xl border border-slate-300 bg-white p-3 text-base text-slate-900 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-600 disabled:opacity-60"
      />
      {interactive && <p id={`${id}-help`} className="mt-1 text-sm text-slate-600">
        Variantni tanlang yoki javobni yozib tahrirlang. Variant tanlash yozilgan javobni almashtiradi.
      </p>}
    </div>
  </div>;
}
