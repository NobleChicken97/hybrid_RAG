"use client";

import { useEffect } from "react";

/**
 * Per-route document titles. All pages are client components (live backend
 * data), so Next's static `metadata` export is unavailable here — this
 * hook keeps the tab title truthful on navigation instead.
 */
export function usePageTitle(title: string) {
  useEffect(() => {
    document.title = `${title} · Hybrid RAG`;
  }, [title]);
}
