import type { Metadata } from "next";
import { JetBrains_Mono, Jost, Mulish } from "next/font/google";
import Link from "next/link";
import "./globals.css";

const display = Jost({
  subsets: ["latin"],
  variable: "--font-jost",
  weight: ["500", "600", "700"],
});

const body = Mulish({
  subsets: ["latin"],
  variable: "--font-mulish",
  weight: ["400", "500", "600", "700"],
});

const mono = JetBrains_Mono({
  subsets: ["latin"],
  variable: "--font-jetbrains-mono",
  weight: ["400", "500", "600"],
});

export const metadata: Metadata = {
  title: "Hybrid RAG System",
  description:
    "Hybrid retrieval (BM25 + vector) with reranking, compression, citations, and RAGAS evaluation.",
};

const NAV = [
  { href: "/", label: "Overview" },
  { href: "/ask", label: "Ask" },
  { href: "/ingest", label: "Ingest" },
  { href: "/eval", label: "Eval" },
  { href: "/system", label: "System" },
  { href: "/topology", label: "Topology" },
];

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body
        className={`${display.variable} ${body.variable} ${mono.variable} min-h-screen bg-abyss font-sans text-ink antialiased`}
      >
        <header className="border-b border-line bg-panel">
          <div className="mx-auto flex max-w-5xl items-center justify-between px-4 py-3">
            <Link href="/" className="flex items-baseline gap-2">
              <span className="font-display text-lg font-semibold tracking-tight text-ink">
                Hybrid&nbsp;RAG
              </span>
              <span className="hidden text-[11px] font-medium uppercase tracking-[0.18em] text-dim sm:inline">
                Retrieval Lab
              </span>
            </Link>
            <nav className="flex gap-1 text-sm">
              {NAV.map((item) => (
                <Link
                  key={item.href}
                  href={item.href}
                  className="rounded-md px-3 py-1.5 font-medium text-mist transition-colors hover:bg-hover hover:text-ink"
                >
                  {item.label}
                </Link>
              ))}
            </nav>
          </div>
          <div className="h-px bg-gradient-to-r from-transparent via-signal/60 to-transparent" />
        </header>
        <main className="mx-auto w-full max-w-5xl flex-1 px-4 py-8">
          {children}
        </main>
        <footer className="border-t border-line-soft bg-panel">
          <div className="mx-auto flex max-w-5xl flex-wrap items-center gap-x-3 gap-y-1 px-4 py-3 text-xs text-dim">
            <span className="font-mono tracking-wide">
              BM25 + Vector → RRF → Reranker → Compression → LLM
            </span>
            <span aria-hidden="true" className="text-line">
              |
            </span>
            <span>
              Backend:{" "}
              <code className="font-mono text-mist">
                {process.env.NEXT_PUBLIC_BACKEND_URL || "/api (same origin)"}
              </code>
            </span>
          </div>
        </footer>
      </body>
    </html>
  );
}
