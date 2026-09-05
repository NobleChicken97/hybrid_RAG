"use client";

import { useEffect, useRef, type ReactNode } from "react";

/**
 * Reveal-on-scroll: sections rise out of a slight blur the first time
 * they enter the viewport (one orchestrated vocabulary, exponential out).
 * Content stays visible by default; nothing hides when motion is reduced
 * or when the observer never fires.
 */
export function Reveal({
  children,
  className,
  delay = 0,
}: {
  children: ReactNode;
  className?: string;
  delay?: number;
}) {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    let cancelled = false;
    let observer: IntersectionObserver | null = null;
    el.style.opacity = "0";
    import("animejs").then(({ animate }) => {
      if (cancelled) return;
      observer = new IntersectionObserver(
        (entries) => {
          for (const entry of entries) {
            if (entry.isIntersecting) {
              animate(entry.target as HTMLElement, {
                opacity: [0, 1],
                translateY: [16, 0],
                filter: ["blur(5px)", "blur(0px)"],
                delay,
                duration: 480,
                ease: "outExpo",
              });
              observer?.disconnect();
            }
          }
        },
        { threshold: 0.12 },
      );
      observer.observe(el);
    });
    return () => {
      cancelled = true;
      observer?.disconnect();
      el.style.opacity = "";
    };
  }, [delay]);

  return (
    <div ref={ref} className={className}>
      {children}
    </div>
  );
}
