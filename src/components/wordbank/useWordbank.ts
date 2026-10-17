import { useCallback, useEffect, useState } from "react";
import { loadWordbank, type WbLoad } from "../../lib/wordbankApi";

/**
 * /api/wordbank/me ni jim o'qiydi (2026-10-16). null — hali yuklanmoqda.
 * reload() — keshni chetlab qayta o'qish (mashq/testdan keyin).
 */
export function useWordbank(fresh = false) {
  const [state, setState] = useState<WbLoad | null>(null);
  const [tick, setTick] = useState(0);

  useEffect(() => {
    let alive = true;
    loadWordbank(fresh || tick > 0).then((v) => {
      if (alive) setState(v);
    });
    return () => {
      alive = false;
    };
  }, [fresh, tick]);

  const reload = useCallback(() => setTick((t) => t + 1), []);
  return { state, reload };
}
