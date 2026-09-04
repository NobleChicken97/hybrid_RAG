import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";

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
      <body className="min-h-screen bg-zinc-50 font-sans text-zinc-900 antialiased">
        <header className="border-b border-zinc-200 bg-white">
          <div className="mx-auto flex max-w-5xl items-center justify-between px-4 py-3">
            <Link href="/" className="text-lg font-semibold tracking-tight">
              🔍 Hybrid RAG
            </Link>
            <nav className="flex gap-1 text-sm">
              {NAV.map((item) => (
                <Link
                  key={item.href}
                  href={item.href}
                  className="rounded px-3 py-1.5 text-zinc-600 hover:bg-zinc-100 hover:text-zinc-950"
                >
                  {item.label}
                </Link>
              ))}
            </nav>
          </div>
        </header>
        <main className="mx-auto w-full max-w-5xl flex-1 px-4 py-8">
          {children}
        </main>
        <footer className="border-t border-zinc-200 bg-white">
          <div className="mx-auto max-w-5xl px-4 py-3 text-xs text-zinc-500">
            BM25 + Vector → RRF → Reranker → Compression → LLM · Backend:{" "}
            <code className="font-mono">
              {process.env.NEXT_PUBLIC_BACKEND_URL || "/api (same origin)"}
            </code>
          </div>
        </footer>
      </body>
    </html>
  );
}
