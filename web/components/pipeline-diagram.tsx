/**
 * Schematic of the real retrieval pipeline. Structure mirrors
 * app/retrieval/pipeline.py: one query fans out to BM25 + vector,
 * fuses with RRF, reranks, compresses, and generates a cited answer.
 * Static geometry, theme-driven fills — no invented data.
 */

const INK = "var(--color-ink)";
const DIM = "var(--color-dim)";
const LINE = "var(--color-line)";
const PANEL = "var(--color-panel)";
const SIGNAL = "var(--color-signal)";
const SIGNAL_INK = "var(--color-signal-ink)";
const GOLD = "var(--color-gold)";

function Node({
  x,
  y,
  w,
  label,
  sub,
  hot = false,
  dark = false,
}: {
  x: number;
  y: number;
  w: number;
  label: string;
  sub: string;
  hot?: boolean;
  dark?: boolean;
}) {
  const h = 52;
  return (
    <g>
      <rect
        x={x}
        y={y}
        width={w}
        height={h}
        style={{
          fill: hot ? SIGNAL : dark ? INK : PANEL,
          stroke: hot ? SIGNAL : LINE,
          strokeWidth: 2,
        }}
      />
      <text
        x={x + w / 2}
        y={y + 23}
        textAnchor="middle"
        style={{
          fill: hot ? SIGNAL_INK : dark ? PANEL : INK,
          fontFamily: "var(--font-mono)",
          fontSize: 13,
          fontWeight: 700,
          letterSpacing: "0.12em",
        }}
      >
        {label}
      </text>
      <text
        x={x + w / 2}
        y={y + 40}
        textAnchor="middle"
        style={{
          fill: hot ? SIGNAL_INK : dark ? PANEL : DIM,
          fontFamily: "var(--font-mono)",
          fontSize: 10.5,
          letterSpacing: "0.08em",
        }}
      >
        {sub}
      </text>
    </g>
  );
}

function Wire({ x1, y1, x2, y2 }: { x1: number; y1: number; x2: number; y2: number }) {
  return (
    <line
      x1={x1}
      y1={y1}
      x2={x2}
      y2={y2}
      style={{ stroke: DIM, strokeWidth: 2 }}
      markerEnd="url(#arrow)"
    />
  );
}

export function PipelineDiagram() {
  const cy = 110; // trunk centerline
  return (
    <svg
      viewBox="0 0 960 220"
      role="img"
      aria-label="Schematic of the hybrid retrieval pipeline"
      className="h-auto w-full font-mono"
    >
      <defs>
        <marker
          id="arrow"
          viewBox="0 0 10 10"
          refX="8"
          refY="5"
          markerWidth="7"
          markerHeight="7"
          orient="auto-start-reverse"
        >
          <path d="M 0 1 L 9 5 L 0 9 z" style={{ fill: DIM }} />
        </marker>
      </defs>
      <Node x={8} y={cy - 26} w={104} label="QUERY" sub="top_k 20" />
      <Node x={152} y={20} w={140} label="BM25" sub="keyword" />
      <Node x={152} y={148} w={140} label="VECTOR" sub="bge-small" />
      <Node x={332} y={cy - 26} w={120} label="RRF" sub="k = 60" />
      <Node x={492} y={cy - 26} w={120} label="RERANK" sub="bge-base · top 5" hot />
      <Node x={652} y={cy - 26} w={120} label="COMPRESS" sub="budget" />
      <Node x={812} y={cy - 26} w={140} label="ANSWER" sub="+ citations" dark />
      <Wire x1={112} y1={cy} x2={146} y2={46} />
      <Wire x1={112} y1={cy} x2={146} y2={174} />
      <Wire x1={292} y1={46} x2={326} y2={cy - 12} />
      <Wire x1={292} y1={174} x2={326} y2={cy + 12} />
      <Wire x1={452} y1={cy} x2={486} y2={cy} />
      <Wire x1={612} y1={cy} x2={646} y2={cy} />
      <Wire x1={772} y1={cy} x2={806} y2={cy} />
      <text
        x={8}
        y={208}
        style={{
          fill: GOLD,
          fontFamily: "var(--font-mono)",
          fontSize: 11,
          letterSpacing: "0.18em",
        }}
      >
        FIG. 01 — THE HONEST PATH FROM QUESTION TO CITED ANSWER
      </text>
    </svg>
  );
}
