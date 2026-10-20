/** Only public question data belongs here. Never inspect answer keys or explanations. */
export type CourseInteractionQuestion = {
  id: string;
  prompt: string;
  mode: 'exact' | 'self';
  options?: string[];
};

export type CourseChoice = { label: string; value: string };

function requiresWrittenOrOrderedAnswer(prompt: string): boolean {
  return (prompt.match(/_{2,}|…|\.\.\./gu) || []).length > 1
    || /\b(?:tartib\p{L}*|joylang|ikki\p{L}*|uchta|vergul|javoblarni|shaklini|qisqartma|reorder|arrange|order|both|multiple)\b|select all|choose all/iu.test(prompt)
    || /\(\s*not\s*\//iu.test(prompt);
}

function labelledChoices(items: string[]): CourseChoice[] | null {
  const matches = items.map(item => /^([A-Z])[).:]\s+(.+)$/u.exec(item));
  if (!matches.every((match, index) => match && match[1] === String.fromCharCode(65 + index))) return null;
  return matches.map(match => ({ label: match![0], value: match![1] }));
}

function explicitChoices(options: string[]): CourseChoice[] {
  // Preserve supplied spelling and labelled letters; do not infer correctness.
  const items = options.map(option => option.trim());
  if (items.length < 2 || items.length > 8 || items.some(item => !item) || new Set(items).size !== items.length) return [];
  const labelled = labelledChoices(items);
  if (labelled) return labelled;
  // Partially labelled lists have an ambiguous submission format.
  if (items.some(item => /^[A-Z][).:]\s/u.test(item))) return [];
  return items.map(label => ({ label, value: label }));
}

/** A narrow lexical list, not dates, fractions, URLs, or grammar notation. */
export function parsePromptChoices(prompt: string): CourseChoice[] {
  if (requiresWrittenOrOrderedAnswer(prompt)) return [];
  const text = prompt.trim();
  // Labelled choices must form the complete trailing block, beginning at A.
  const start = /(?:^|[\n:]\s*)A[).:]\s+/u.exec(text);
  if (start) {
    const block = text.slice(start.index).replace(/^[\n:]\s*/u, '');
    const items = block.split(/\s+(?=[A-Z][).:]\s)/u).map(item => item.trim());
    const labelled = labelledChoices(items);
    if (labelled && labelled.length >= 2 && labelled.length <= 8) return labelled;
    return [];
  }
  if ((text.match(/\//gu) || []).length < 1) return [];
  // Accept exactly one terminal parenthesized list, or a whole/colon-tail list.
  const parenthesized = /\(([^()]*)\)[.!?]?$/u.exec(text);
  let candidate: string;
  if (parenthesized) {
    if (text.slice(0, parenthesized.index).includes('/')) return [];
    candidate = parenthesized[1];
  } else {
    const colon = text.lastIndexOf(':');
    candidate = text.slice(colon + 1).replace(/[.!?]$/u, '').trim();
    if (colon >= 0 && text.slice(0, colon).includes('/')) return [];
  }
  // Spaces on both sides are required. Each choice is one short lexical word.
  // This intentionally leaves sentences and ambiguous slash notation as writing.
  const items = candidate.split(/\s+\/\s+/u);
  if (items.length < 2 || items.length > 6 || items.some(item => !/^\p{L}[\p{L}'’‘ʻʼ-]{0,29}$/u.test(item))) return [];
  if (new Set(items.map(item => item.toLocaleLowerCase('en'))).size !== items.length) return [];
  const notation = new Set(['and/or', 'he/she', 'his/her', 'him/her', 's/v', 'v/o', 'subject/verb', 'singular/plural', 'present/past', 'noun/verb']);
  if (notation.has(items.map(item => item.toLowerCase()).join('/'))) return [];
  if (items.some(item => /^[A-Z]+$/u.test(item))) return [];
  return items.map(label => ({ label, value: label }));
}

export function getCourseQuestionChoices(question: CourseInteractionQuestion): CourseChoice[] {
  // "self" does not specify a single-answer contract. Never convert it to radios
  // or invent a serialization for multiple selections.
  if (question.mode !== 'exact' || requiresWrittenOrOrderedAnswer(question.prompt)) return [];
  // An explicit but malformed list must not silently fall through to inference.
  return question.options !== undefined ? explicitChoices(question.options) : parsePromptChoices(question.prompt);
}

/** Exact comparison keeps arbitrary drafts untouched and avoids claiming correctness. */
export function selectedCourseChoice(choices: CourseChoice[], value: string): number {
  return choices.findIndex(choice => choice.value === value);
}

/** Ordering is supported only when both the instruction and letter contract exist. */
export function getCourseQuestionOrdering(question: CourseInteractionQuestion): CourseChoice[] {
  if (question.mode !== 'self' || !question.options || !/\b(?:qaysi\s+tartibda|tartibini)\b/iu.test(question.prompt)) return [];
  const items = question.options.map(option => option.trim());
  if (items.length < 2 || items.length > 8) return [];
  return labelledChoices(items) || [];
}

export function parseCourseQuestionOrder(choices: CourseChoice[], value: string): string[] {
  if (!value.trim()) return [];
  const letters = value.split(',').map(letter => letter.trim());
  if (new Set(letters).size !== letters.length || letters.some(letter => !choices.some(choice => choice.value === letter))) return [];
  return letters;
}

export type CourseOrderAction = { type: 'toggle'; value: string } | { type: 'undo' } | { type: 'reset' };

export function changeCourseQuestionOrder(choices: CourseChoice[], value: string, action: CourseOrderAction): string {
  if (action.type === 'reset') return '';
  const order = parseCourseQuestionOrder(choices, value);
  if (action.type === 'undo') return order.length ? order.slice(0, -1).join(', ') : value;
  if (!choices.some(choice => choice.value === action.value)) return value;
  return (order.includes(action.value) ? order.filter(letter => letter !== action.value) : [...order, action.value]).join(', ');
}

/** Explicit word-order instruction and literal token list; never fabricate tokens. */
export function getCourseWordOrder(question: CourseInteractionQuestion): CourseChoice[] {
  if (question.mode !== 'exact' || question.options !== undefined) return [];
  const match = /^(?:Gapni tartiblang|So[‘’ʻʼ']zlarni odatiy tartibda joylang):\s*(.+?)[.!?]?$/iu.exec(question.prompt.trim());
  if (!match) return [];
  const tokens = match[1].split(/\s+\/\s+/u);
  if (tokens.length < 2 || tokens.length > 16 || tokens.some(token => !/^\p{L}[\p{L}'’‘ʻʼ-]*$/u.test(token))) return [];
  // Occurrence IDs, not text, retain repeated words as separate available tokens.
  return tokens.map((label, index) => ({ label, value: String(index) }));
}

export function parseCourseWordOrder(choices: CourseChoice[], value: string): string[] {
  if (!value.trim()) return [];
  const remaining = [...choices];
  const ids: string[] = [];
  for (const token of value.trim().split(/\s+/u)) {
    const index = remaining.findIndex(choice => choice.label === token);
    if (index < 0) return [];
    ids.push(remaining[index].value);
    remaining.splice(index, 1);
  }
  return ids;
}

export function changeCourseWordOrder(choices: CourseChoice[], value: string, action: CourseOrderAction): string {
  if (action.type === 'reset') return '';
  const order = parseCourseWordOrder(choices, value);
  if (action.type === 'undo' && !order.length) return value;
  if (action.type === 'toggle' && !choices.some(choice => choice.value === action.value)) return value;
  const next = action.type === 'undo' ? order.slice(0, -1)
    : order.includes(action.value) ? order.filter(id => id !== action.value) : [...order, action.value];
  return next.map(id => choices.find(choice => choice.value === id)!.label).join(' ');
}
