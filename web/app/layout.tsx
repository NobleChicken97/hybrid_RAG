import type { Metadata } from "next";
import { Archivo, JetBrains_Mono, Mulish } from "next/font/google";
import Link from "next/link";
import "./globals.css";

const display = Archivo({
  subsets: ["latin"],
  variable: "--font-head",
  weight: ["600", "700", "800"],
});

const body = Mulish({
  subsets: ["latin"],
  variable: "--font-body",
  weight: ["400", "500", "600", "700"],
});

const mono = JetBrains_Mono({
  subsets: ["latin"],
  variable: "--font-code",
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
        <header className="border-b-2 border-line bg-panel">
          <div className="mx-auto flex max-w-6xl items-stretch justify-between px-4">
            <Link href="/" className="flex items-center gap-3 py-3">
              <span
                aria-hidden="true"
                className="flex h-8 w-8 items-center justify-center bg-signal font-display text-lg font-extrabold text-signal-ink"
              >
                R
              </span>
              <span className="flex flex-col leading-none">
                <span className="font-display text-lg font-bold tracking-tight text-ink">
                  HYBRID&nbsp;RAG
                </span>
                <span className="text-[10px] font-semibold uppercase tracking-[0.24em] text-dim">
                  Retrieval Lab
                </span>
              </span>
            </Link>
            <nav className="flex items-stretch text-[13px] font-semibold uppercase tracking-[0.12em]">
              {NAV.map((item) => (
                <Link
                  key={item.href}
                  href={item.href}
                  className="flex items-center border-l border-line-soft px-4 text-mist transition-colors last:border-r hover:bg-hover hover:text-signal"
                >
                  {item.label}
                </Link>
              ))}
            </nav>
          </div>
          <div className="h-[3px] bg-signal" />
        </header>
        <main className="mx-auto w-full max-w-6xl flex-1 px-4 py-6">
          {children}
        </main>
        <footer className="border-t border-line bg-panel">
          <div className="mx-auto flex max-w-6xl flex-wrap items-center gap-x-3 gap-y-1 px-4 py-3 font-mono text-[11px] tracking-wide text-dim">
            <span>
              BM25 + VECTOR → RRF → RERANKER → COMPRESSION → LLM
            </span>
            <span aria-hidden="true" className="text-line">
              ▪
            </span>
            <span>
              BACKEND:{" "}
              <span className="text-mist">
                {process.env.NEXT_PUBLIC_BACKEND_URL || "/api (same origin)"}
              </span>
            </span>
          </div>
        </footer>
      </body>
    </html>
  );
}
