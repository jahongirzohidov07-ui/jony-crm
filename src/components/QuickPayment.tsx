import { useEffect, useRef, useState } from "react";
import { Wallet, X, Search, Check } from "lucide-react";
import { printXReceipt } from "../lib/receipt";
import { api, newClientKey, ApiError, type Student } from "../lib/api";
import { formatSom } from "../lib/format";
import { PAYMENT_METHODS } from "../lib/payments";
import { formatPhone } from "./PhoneInput";

/**
 * Tez to'lov. Administratorning kuni shu tugmadan boshlanadi: o'quvchini
 * qidiradi, summani yozadi, tamom. Talabalar bo'limiga o'tish, kartani
 * ochish, tabni topish — bularning hammasi olib tashlangan.
 */
export function QuickPayment({
  onDone,
  trigger = "button",
}: {
  onDone?: () => void;
  trigger?: "button" | "compact";
}) {
  const [open, setOpen] = useState(false);
  return (
    <>
      {trigger === "compact" ? (
        <button
          onClick={() => setOpen(true)}
          title="To'lov qabul qilish"
          className="w-9 h-9 rounded-lg bg-brand-600 text-white flex items-center justify-center hover:bg-brand-700"
        >
          <Wallet size={16} />
        </button>
      ) : (
        <button
          onClick={() => setOpen(true)}
          data-guide="btn-take-payment"
          className="flex items-center gap-2 px-4 py-2.5 rounded-lg bg-brand-600 text-white text-sm font-medium hover:bg-brand-700 shadow-sm"
        >
          <Wallet size={16} />
          To'lov qabul qilish
        </button>
      )}
      {open && (
        <PaymentModal
          onClose={() => setOpen(false)}
          onSaved={() => {
            setOpen(false);
            onDone?.();
          }}
        />
      )}
    </>
  );
}

function PaymentModal({
  onClose,
  onSaved,
  student: fixed,
}: {
  onClose: () => void;
  onSaved: () => void;
  student?: Student;
}) {
  const [all, setAll] = useState<Student[]>([]);
  const [q, setQ] = useState("");
  const [picked, setPicked] = useState<Student | null>(fixed ?? null);
  const [amount, setAmount] = useState("");
  const [method, setMethod] = useState("cash");
  const [note, setNote] = useState("");
  const [books, setBooks] = useState<
    { id: number; name: string; qty: number }[]
  >([]);
  const [bookId, setBookId] = useState("");
  const [saving, setSaving] = useState(false);
  const [err, setErr] = useState("");
  const [ok, setOk] = useState(false);
  const searchRef = useRef<HTMLInputElement>(null);
  // Dubl to'lovga qarshi idempotentlik kaliti — muvaffaqiyatli
  // saqlangandan keyingina yangilanadi (2026-08-14).
  const payKey = useRef<string>(newClientKey());

  useEffect(() => {
    api
      .get<{ id: number; name: string; qty: number }[]>("/consumables/books")
      .then(setBooks)
      .catch(() => setBooks([]));
  }, []);

  useEffect(() => {
    if (fixed) return;
    api
      .get<Student[]>("/students")
      .then((s) => setAll(s.filter((x) => x.status !== "archived")))
      .catch(() => setAll([]));
    setTimeout(() => searchRef.current?.focus(), 50);
  }, [fixed]);

  const found = q.trim()
    ? all
        .filter((s) => {
          const t = q.toLowerCase();
          return (
            s.full_name.toLowerCase().includes(t) ||
            (s.phone || "").includes(t) ||
            (s.public_id || "").toLowerCase().includes(t)
          );
        })
        .slice(0, 8)
    : [];

  async function save() {
    const v = Number(amount);
    if (!picked) {
      setErr("O'quvchini tanlang");
      return;
    }
    if (!v || v <= 0) {
      setErr("To'g'ri summa kiriting");
      return;
    }
    setSaving(true);
    setErr("");
    try {
      // DUBL HIMOYASI (2026-08-14): bir xil kalit bilan yuborilgan
      // takroriy so'rov serverda ikkinchi to'lov ochmaydi.
      const body = {
        amount: v,
        kind: "payment",
        method,
        note: note || null,
        client_key: payKey.current,
        force: false,
      };
      let created: { id?: number } = {};
      try {
        created = await api.post<{ id?: number }>(
          `/students/${picked.id}/payments`,
          body
        );
      } catch (dup) {
        // Server "hozirgina xuddi shunday to'lov kiritilgan" desa —
        // xodimdan aniq so'raymiz, tasdiqlasa o'tkazamiz.
        if (
          dup instanceof ApiError &&
          dup.status === 409 &&
          dup.canForce &&
          confirm(dup.message + "\n\nBaribir kiritilsinmi?")
        ) {
          created = await api.post<{ id?: number }>(
            `/students/${picked.id}/payments`,
            { ...body, client_key: newClientKey(), force: true }
          );
        } else {
          throw dup;
        }
      }
      payKey.current = newClientKey(); // keyingi to'lov uchun yangi kalit
      // Kitob berilgan bo'lsa — ombordan kamaytiramiz
      if (bookId) {
        try {
          await api.post(`/consumables/${bookId}/give-book`, {
            student_id: picked.id,
          });
        } catch (be) {
          alert(
            be instanceof Error
              ? be.message
              : "Kitobni ombordan yechishda xatolik"
          );
        }
      }
      // X-printer chek: xohlasa darrov chiqarib beradi
      if (confirm("Chek chiqarilsinmi?")) {
        printXReceipt({
          student: picked.full_name,
          publicId: (picked as { public_id?: string | null }).public_id,
          amount: v,
          method,
          note: note || null,
          balance:
            (picked as { balance?: number | null }).balance != null
              ? ((picked as { balance?: number }).balance ?? 0) + v
              : null,
          cashier: undefined,
          paymentId: created?.id ?? null,
        });
      }
      setOk(true);
      setTimeout(onSaved, 900);
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Xatolik");
      setSaving(false);
    }
  }

  return (
    <div className="fixed inset-0 bg-black/30 flex items-start justify-center z-50 p-4 pt-20">
      <div className="bg-white rounded-xl w-full max-w-md p-5 shadow-xl">
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-semibold text-slate-800 flex items-center gap-2">
            <Wallet size={17} className="text-brand-600" />
            To'lov qabul qilish
          </h3>
          <button onClick={onClose} className="text-slate-400">
            <X size={18} />
          </button>
        </div>

        {ok ? (
          <div className="py-8 text-center">
            <div className="w-14 h-14 rounded-full bg-emerald-100 text-emerald-600 flex items-center justify-center mx-auto mb-3">
              <Check size={26} />
            </div>
            <p className="text-sm font-medium text-slate-800">
              {formatSom(Number(amount))} qabul qilindi
            </p>
            <p className="text-xs text-slate-500 mt-0.5">{picked?.full_name}</p>
          </div>
        ) : (
          <>
            {err && (
              <p className="text-sm text-red-600 bg-red-50 rounded-lg px-3 py-2 mb-3">
                {err}
              </p>
            )}

            {!picked ? (
              <div>
                <div className="flex items-center gap-2 px-3 py-2 rounded-lg border border-slate-200 mb-2">
                  <Search size={15} className="text-slate-400" />
                  <input
                    ref={searchRef}
                    value={q}
                    onChange={(e) => setQ(e.target.value)}
                    placeholder="Ism, telefon yoki ID bo'yicha qidiring"
                    className="flex-1 text-sm outline-none"
                  />
                </div>
                {q.trim() && found.length === 0 && (
                  <p className="text-sm text-slate-400 py-4 text-center">
                    Topilmadi
                  </p>
                )}
                <div className="space-y-1 max-h-72 overflow-y-auto">
                  {found.map((s) => (
                    <button
                      key={s.id}
                      onClick={() => setPicked(s)}
                      className="w-full text-left px-3 py-2 rounded-lg hover:bg-slate-50 border border-transparent hover:border-slate-200"
                    >
                      <div className="flex items-center justify-between gap-2">
                        <span className="text-sm text-slate-800">
                          {s.full_name}
                        </span>
                        <span
                          className={`text-sm font-medium ${
                            s.balance < 0 ? "text-red-600" : "text-slate-500"
                          }`}
                        >
                          {formatSom(s.balance)}
                        </span>
                      </div>
                      <p className="text-xs text-slate-400">
                        {[s.group?.name, formatPhone(s.phone)]
                          .filter(Boolean)
                          .join(" · ")}
                      </p>
                    </button>
                  ))}
                </div>
              </div>
            ) : (
              <div className="space-y-3">
                <div className="flex items-center justify-between px-3 py-2.5 rounded-lg bg-slate-50">
                  <div>
                    <p className="text-sm font-medium text-slate-800">
                      {picked.full_name}
                    </p>
                    <p className="text-xs text-slate-500">
                      {picked.group?.name || "guruhsiz"}
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="text-xs text-slate-500">Balans</p>
                    <p
                      className={`text-sm font-medium ${
                        picked.balance < 0 ? "text-red-600" : "text-emerald-600"
                      }`}
                    >
                      {formatSom(picked.balance)}
                    </p>
                  </div>
                  {!fixed && (
                    <button
                      onClick={() => setPicked(null)}
                      className="ml-2 text-xs text-brand-600 hover:underline"
                    >
                      o'zgartirish
                    </button>
                  )}
                </div>

                {picked.balance < 0 && (
                  <button
                    onClick={() => setAmount(String(Math.abs(picked.balance)))}
                    className="w-full py-2 rounded-lg border border-brand-200 bg-brand-50 text-sm text-brand-700 hover:border-brand-400"
                  >
                    Butun qarzni yopish — {formatSom(Math.abs(picked.balance))}
                  </button>
                )}

                <div>
                  <label className="block text-xs text-slate-500 mb-1">
                    Summa
                  </label>
                  <input
                    type="number"
                    value={amount}
                    onChange={(e) => setAmount(e.target.value)}
                    placeholder="480000"
                    autoFocus
                    className="w-full px-3 py-2.5 rounded-lg border border-slate-200 text-base"
                  />
                </div>

                <div>
                  <label className="block text-xs text-slate-500 mb-1">
                    To'lov usuli
                  </label>
                  <div className="flex gap-1.5">
                    {PAYMENT_METHODS.map((m) => (
                      <button
                        key={m.key}
                        onClick={() => setMethod(m.key)}
                        className={`flex-1 px-2 py-2 rounded-lg text-xs font-medium border transition ${
                          method === m.key
                            ? "bg-brand-50 border-brand-400 text-brand-700"
                            : "bg-white border-slate-200 text-slate-500 hover:border-slate-300"
                        }`}
                      >
                        {m.label}
                      </button>
                    ))}
                  </div>
                </div>

                {books.length > 0 && (
                  <div>
                    <label className="block text-xs text-slate-500 mb-1">
                      Kitob berildimi?
                    </label>
                    <select
                      value={bookId}
                      onChange={(e) => setBookId(e.target.value)}
                      className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm bg-white"
                    >
                      <option value="">— kitob berilmadi —</option>
                      {books.map((b) => (
                        <option key={b.id} value={b.id}>
                          {b.name} (qoldiq: {b.qty})
                        </option>
                      ))}
                    </select>
                    {bookId &&
                      (books.find((b) => String(b.id) === bookId)?.qty ?? 0) <
                        1 && (
                        <p className="text-xs text-red-600 mt-1">
                          Omborda yo'q! Filial rahbariga ayting — avval kirim
                          qilinsin.
                        </p>
                      )}
                  </div>
                )}

                <input
                  value={note}
                  onChange={(e) => setNote(e.target.value)}
                  placeholder="Izoh (ixtiyoriy)"
                  className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm"
                />

                <button
                  onClick={save}
                  disabled={saving}
                  className="w-full py-2.5 rounded-lg bg-brand-600 text-white text-sm font-medium hover:bg-brand-700 disabled:opacity-50"
                >
                  {saving ? "Saqlanmoqda..." : "To'lovni qabul qilish"}
                </button>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}

/**
 * O'quvchi allaqachon tanlangan holdagi to'lov oynasi. Ro'yxatdagi
 * "uch nuqta" menyusi kabi joylardan chaqiriladi - administrator
 * o'quvchi kartasiga o'tib o'tirmasin (Jahongir, 2026-08-12:
 * "qoshish uchun joy bolsin oson bolsin topish").
 */
export function StudentPayModal({
  student,
  onClose,
  onSaved,
}: {
  student: Student;
  onClose: () => void;
  onSaved?: () => void;
}) {
  return (
    <PaymentModal
      student={student}
      onClose={onClose}
      onSaved={() => {
        onClose();
        onSaved?.();
      }}
    />
  );
}

/** O'quvchi kartasidan to'lov: qidiruvsiz, darrov summa so'raydi. */
export function StudentPayButton({
  student,
  onDone,
}: {
  student: Student;
  onDone?: () => void;
}) {
  const [open, setOpen] = useState(false);
  return (
    <>
      <button
        onClick={() => setOpen(true)}
        className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-brand-600 text-white text-sm font-medium hover:bg-brand-700"
      >
        <Wallet size={14} /> To'lov
      </button>
      {open && (
        <PaymentModal
          student={student}
          onClose={() => setOpen(false)}
          onSaved={() => {
            setOpen(false);
            onDone?.();
          }}
        />
      )}
    </>
  );
}
