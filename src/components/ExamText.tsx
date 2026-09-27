import { Fragment, type ReactNode } from "react";
import type { BoxLine, Group, InsLine, Opt, Run } from "../lib/examFormat";

/**
 * CAMBRIDGE KO'RINISHIDAGI KO'RSATMALAR (2026-09-27) — lib/examFormat.ts
 * ajratgan tuzilmani chizadi. Qoidalar o'sha faylning boshida.
 */

/** Qator bo'laklari: qalin joylar va bo'sh joy (gap) chizig'i. */
export function Runs({ runs }: { runs: Run[] }) {
  return (
    <>
      {runs.map((r, i) =>
        r.gap ? (
          <span key={i} className="whitespace-nowrap">
            {r.t ? <strong className="font-bold not-italic">{r.t}</strong> : null}
            <span
              aria-hidden="true"
              className="inline-block w-16 mx-1 border-b border-dotted border-slate-500 align-baseline"
            />
          </span>
        ) : r.b ? (
          <strong key={i} className="font-bold">
            {r.t}
          </strong>
        ) : (
          <Fragment key={i}>{r.t}</Fragment>
        )
      )}
    </>
  );
}

const runsText = (runs: Run[]) => runs.map((r) => r.t).join("");

/** Bir turdagi ketma-ket qatorlarni bitta jadvalga yig'adi. */
function groupRuns<T extends { k: string }>(items: T[], kind: string): (T | T[])[] {
  const out: (T | T[])[] = [];
  for (const it of items) {
    const last = out[out.length - 1];
    if (it.k === kind && Array.isArray(last)) last.push(it);
    else out.push(it.k === kind ? [it] : it);
  }
  return out;
}

function OptRow({ o }: { o: Opt }) {
  return (
    <>
      <span className="font-bold text-slate-900">{o.letter}</span>
      <span>
        <Runs runs={o.runs} />
      </span>
    </>
  );
}

function Box({ lines }: { lines: BoxLine[] }) {
  const items = groupRuns(lines, "opt");
  return (
    <div className="mt-3 rounded-sm border border-slate-400/80 bg-white/60 px-4 py-3 text-slate-800">
      <div className="space-y-1.5">
        {items.map((it, i): ReactNode => {
          if (Array.isArray(it))
            return (
              <div key={i} className="grid grid-cols-[auto_1fr] gap-x-3 gap-y-1 pl-1">
                {it.map((x, j) => (x.k === "opt" ? <OptRow key={j} o={x.opt} /> : null))}
              </div>
            );
          switch (it.k) {
            case "title":
              return (
                <p key={i} className="text-center font-bold text-[1.05em] text-slate-900 pb-1">
                  <Runs runs={it.runs} />
                </p>
              );
            case "sub":
              return (
                <p key={i} className="font-bold text-slate-900 pt-1.5">
                  <Runs runs={it.runs} />
                </p>
              );
            case "bullet":
              return (
                <div key={i} className={`flex gap-2 ${it.level === 2 ? "pl-6" : ""}`}>
                  <span aria-hidden="true" className="shrink-0 text-slate-500">
                    {it.level === 2 ? "–" : "•"}
                  </span>
                  <span className="min-w-0">
                    <Runs runs={it.runs} />
                  </span>
                </div>
              );
            case "opts":
              return (
                <div key={i} className="flex flex-wrap gap-x-6 gap-y-1 pl-1">
                  {it.opts.map((o, j) => (
                    <span key={j}>
                      <span className="font-bold text-slate-900 mr-2">{o.letter}</span>
                      <Runs runs={o.runs} />
                    </span>
                  ))}
                </div>
              );
            case "opt":
              return null;
            default:
              return (
                <p key={i}>
                  <Runs runs={it.runs} />
                </p>
              );
          }
        })}
      </div>
    </div>
  );
}

function Line({ l }: { l: InsLine }) {
  switch (l.k) {
    case "heading":
      return (
        <p className="font-bold uppercase tracking-wider text-slate-900">
          <Runs runs={l.runs} />
        </p>
      );
    case "ins":
      return (
        <p className="italic text-slate-700">
          <Runs runs={l.runs} />
        </p>
      );
    case "nb":
      return (
        <p className="text-slate-700">
          <strong className="font-bold text-slate-900 mr-2">NB</strong>
          <span className="italic">
            <Runs runs={l.runs} />
          </span>
        </p>
      );
    case "stem":
      return (
        <p className="text-slate-900">
          <Runs runs={l.runs} />
        </p>
      );
    default:
      return null;
  }
}

/**
 * Bitta savollar guruhi: "Questions 8–13" (kursiv), ko'rsatmalar, ramka.
 * skipHeading — bo'lim nomi (masalan "Reading Passage 1") tepada allaqachon
 * chiqqan bo'lsa, ko'rsatmadagi o'sha sarlavha takrorlanmaydi.
 */
export function InstructionGroup({ g, skipHeading }: { g: Group; skipHeading?: string }) {
  const skip = (skipHeading || "").trim().toLowerCase();
  const lines = g.lines.filter(
    (l) => !(l.k === "heading" && skip && runsText(l.runs).trim().toLowerCase() === skip)
  );
  if (!g.label && !lines.length && !g.box.length) return null;
  const items = groupRuns(lines, "key");
  return (
    <div className="text-sm leading-relaxed text-slate-800">
      {g.label ? (
        <p className="italic text-[1.08em] font-medium text-slate-900 mb-2">{g.label}</p>
      ) : null}
      <div className="space-y-2">
        {items.map((it, i) =>
          Array.isArray(it) ? (
            <div key={i} className="grid grid-cols-[auto_1fr] gap-x-4 gap-y-0.5 pl-4">
              {it.map((l, j) =>
                l.k === "key" ? (
                  <Fragment key={j}>
                    <span className="font-bold italic text-slate-900">{l.key}</span>
                    <span className="italic text-slate-700">
                      <Runs runs={l.runs} />
                    </span>
                  </Fragment>
                ) : null
              )}
            </div>
          ) : (
            <Line key={i} l={it} />
          )
        )}
      </div>
      {g.box.length ? <Box lines={g.box} /> : null}
    </div>
  );
}
