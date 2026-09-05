"use client";

import { animate } from "animejs";
import { useEffect, useRef } from "react";

/**
 * Animated numeral: counts from 0 to `value` on mount/change.
 * Static text when value is null (caller passes its own fallback),
 * instant final value when the user prefers reduced motion.
 */
export function CountUp({
  value,
  decimals = 0,
  className,
}: {
  value: number | null | undefined;
  decimals?: number;
  className?: string;
}) {
  const ref = useRef<HTMLSpanElement>(null);

  useEffect(() => {
    const el = ref.current;
    if (!el || value == null) return;
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
      el.textContent = value.toFixed(decimals);
      return;
    }
    const obj = { v: 0 };
    const anim = animate(obj, {
      v: value,
      duration: 900,
      ease: "outExpo",
      onUpdate: () => {
        el.textContent = obj.v.toFixed(decimals);
      },
    });
    return () => {
      anim.pause();
    };
  }, [value, decimals]);

  if (value == null) return null;
  return (
    <span ref={ref} className={className}>
      {value.toFixed(decimals)}
    </span>
  );
}
