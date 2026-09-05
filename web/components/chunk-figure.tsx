/**
 * The cataloging act, drawn: one source sheet fans out into three
 * indexed chunk slips, each stamped with its call number. Static
 * geometry, theme-driven fills — the motion budget lives elsewhere.
 */

const INK = "var(--color-ink)";
const DIM = "var(--color-dim)";
const LINE = "var(--color-line)";
const PAPER = "var(--color-raised)";
const BRASS = "var(--color-gold)";
const SIGNAL = "var(--color-signal)";
const SIGNAL_INK = "var(--color-signal-ink)";

function Slip({
  x,
  y,
  callNo,
  lines,
}: {
  x: number;
  y: number;
  callNo: string;
  lines: number[];
}) {
  return (
    <g>
      <rect
        x={x}
        y={y}
        width={150}
        height={64}
        style={{ fill: PAPER, stroke: LINE, strokeWidth: 2 }}
      />
      <rect
        x={x}
        y={y}
        width={150}
        height={18}
        style={{ fill: SIGNAL }}
      />
      <text
        x={x + 8}
        y={y + 13}
        style={{
          fill: SIGNAL_INK,
          fontFamily: "var(--font-mono)",
          fontSize: 9.5,
          fontWeight: 700,
          letterSpacing: "0.1em",
        }}
      >
        {callNo}
      </text>
      {lines.map((w, i) => (
        <rect
          key={i}
          x={x + 8}
          y={y + 26 + i * 9}
          width={w}
          height={4}
          style={{ fill: DIM, opacity: 0.7 }}
        />
      ))}
    </g>
  );
}

export function ChunkFigure() {
  return (
    <svg
      viewBox="0 0 400 300"
      role="img"
      aria-label="A source document fanning out into three indexed chunk slips"
      className="h-auto w-full"
    >
      {/* source sheet */}
      <rect
        x={16}
        y={60}
        width={120}
        height={180}
        style={{ fill: PAPER, stroke: INK, strokeWidth: 2.5 }}
      />
      <rect x={16} y={60} width={120} height={26} style={{ fill: INK }} />
      <text
        x={28}
        y={77}
        style={{
          fill: PAPER,
          fontFamily: "var(--font-mono)",
          fontSize: 10,
          fontWeight: 700,
          letterSpacing: "0.14em",
        }}
      >
        SOURCE DOC
      </text>
      {[0, 1, 2, 3, 4, 5, 6].map((i) => (
        <rect
          key={i}
          x={28}
          y={98 + i * 19}
          width={96 - (i % 3) * 14}
          height={5}
          style={{ fill: DIM, opacity: 0.75 }}
        />
      ))}
      {/* fan wires */}
      <line x1={136} y1={120} x2={218} y2={42} style={{ stroke: DIM, strokeWidth: 2 }} markerEnd="url(#chip-arrow)" />
      <line x1={136} y1={150} x2={218} y2={138} style={{ fill: "none", stroke: DIM, strokeWidth: 2 }} markerEnd="url(#chip-arrow)" />
      <line x1={136} y1={180} x2={218} y2={240} style={{ stroke: DIM, strokeWidth: 2 }} markerEnd="url(#chip-arrow)" />
      <defs>
        <marker
          id="chip-arrow"
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
      <Slip x={224} y={10} callNo="CHUNK_0000" lines={[120, 134, 104]} />
      <Slip x={224} y={112} callNo="CHUNK_0001" lines={[134, 96, 120]} />
      <Slip x={224} y={214} callNo="CHUNK_0002" lines={[110, 134, 90]} />
      <text
        x={16}
        y={294}
        style={{
          fill: BRASS,
          fontFamily: "var(--font-mono)",
          fontSize: 11,
          letterSpacing: "0.18em",
        }}
      >
        FIG. 02 — ONE SHEET, INDEXED THREE WAYS
      </text>
    </svg>
  );
}
