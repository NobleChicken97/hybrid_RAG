import type { Metadata } from "next";
import { Oswald, Roboto_Mono, Saira } from "next/font/google";
import Link from "next/link";
import "./globals.css";

const display = Oswald({
  subsets: ["latin"],
  variable: "--font-head",
  weight: ["500", "600", "700"],
});

const body = Saira({
  subsets: ["latin"],
  variable: "--font-body",
  weight: ["400", "500", "600", "700"],
});

const mono = Roboto_Mono({
  subsets: ["latin"],
  variable: "--font-code",
  weight: ["400", "500", "600"],
});

export const metadata: Metadata = {
  metadataBase: new URL("https://rag.noblechicken.me"),
  title: {
    default: "Hybrid RAG System",
    template: "%s · Hybrid RAG",
  },
  description:
    "Hybrid retrieval (BM25 + vector) with reranking, compression, citations, and RAGAS evaluation.",
  openGraph: {
    title: "Hybrid RAG System",
    description:
      "Ask questions over your documents; every answer carries citations and a full retrieval debug trace.",
    type: "website",
  },
  twitter: {
    card: "summary",
    title: "Hybrid RAG System",
    description:
      "Hybrid retrieval (BM25 + vector) with reranking, compression, citations, and RAGAS evaluation.",
  },
};

export const viewport = {
  themeColor: "#F2EAD8",
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
        className={`${display.variable} ${body.variable} ${mono.variable} flex min-h-screen flex-col bg-abyss font-sans text-ink antialiased`}
      >
        <div className="bg-console text-console-mist">
          <div className="flex w-full items-center justify-between px-4 py-1.5 font-mono text-[10px] uppercase tracking-[0.24em]">
            <span>Retrieval reading room</span>
            <span>
              Backend{" "}
              <span className="text-console-ink">
                {process.env.NEXT_PUBLIC_BACKEND_URL || "/api (same origin)"}
              </span>
            </span>
          </div>
        </div>
        <header className="border-b-4 border-signal bg-abyss">
          <div className="flex w-full flex-wrap items-end justify-between gap-4 px-4 pb-4 pt-5">
            <Link href="/" className="flex items-center gap-3">
              <span
                aria-hidden="true"
                className="bg-signal px-2.5 py-1 font-display text-2xl font-bold leading-none text-signal-ink"
              >
                HR
              </span>
              <span className="font-display text-3xl font-bold uppercase leading-none tracking-tight text-ink">
                Hybrid&nbsp;RAG
              </span>
            </Link>
            <nav className="flex flex-wrap border border-line">
              {NAV.map((item) => (
                <Link
                  key={item.href}
                  href={item.href}
                  className="border-l border-line px-4 py-2 text-[13px] font-bold uppercase tracking-[0.14em] text-mist transition-colors first:border-l-0 hover:bg-ink hover:text-abyss"
                >
                  {item.label}
                </Link>
              ))}
            </nav>
          </div>
        </header>
        <main className="w-full flex-1 px-4 py-6">
          {children}
        </main>
        <footer className="bg-console text-console-mist">
          <div className="flex w-full flex-wrap items-center gap-x-3 gap-y-1 px-4 py-4 font-mono text-[11px] tracking-wide">
            <span>BM25 + VECTOR · RRF · RERANKER · COMPRESSION · LLM</span>
            <span aria-hidden="true" className="text-signal">
              ·
            </span>
            <span>SET IN OSWALD, SAIRA & ROBOTO MONO · PRINTED ON PIXELS</span>
          </div>
        </footer>
      </body>
    </html>
  );
}
