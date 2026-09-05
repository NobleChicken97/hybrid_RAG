"use client";

import { useEffect, useRef, useState } from "react";

/**
 * Ledger ticker: rotates through live run records with a soft
 * crossfade (one shared motion vocabulary with the reveals).
 * Static first record when motion is reduced or there is one item.
 */
export function Ticker({ items }: { items: { top: string; bottom: string }[] }) {
  const [index, setIndex] = useState(0);
  const boxRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (items.length < 2) return;
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    let cancelled = false;
    let timer: ReturnType<typeof setInterval> | null = null;
    import("animejs").then(({ animate }) => {
      if (cancelled) return;
      timer = setInterval(() => {
        const el = boxRef.current;
        if (!el) return;
        animate(
          el,
          {
            opacity: [1, 0],
            translateY: [0, -6],
            duration: 260,
            ease: "inExpo",
            onComplete: () => {
              if (cancelled) return;
              setIndex((i) => (i + 1) % items.length);
              animate(
                el,
                {
                  opacity: [0, 1],
                  translateY: [8, 0],
                  duration: 420,
                  ease: "outExpo",
                },
              );
            },
          },
        );
      }, 4600);
    });
    return () => {
      cancelled = true;
      if (timer) clearInterval(timer);
    };
  }, [items.length]);

  const current = items[Math.min(index, items.length - 1)] ?? {
    top: "No audits yet",
    bottom: "Run the holdings against the question set to file the first slip.",
  };

  return (
    <div className="flex items-stretch gap-px bg-console-line">
      <div className="flex items-center bg-signal px-3">
        <span className="font-mono text-[10px] font-bold uppercase tracking-[0.2em] text-signal-ink">
          Live
        </span>
      </div>
      <div ref={boxRef} className="flex-1 bg-console px-4 py-2.5">
        <div className="font-mono text-xs font-semibold text-console-ink">
          {current.top}
        </div>
        <div className="mt-0.5 font-mono text-[11px] tabular-nums text-console-mist">
          {current.bottom}
        </div>
      </div>
    </div>
  );
}
