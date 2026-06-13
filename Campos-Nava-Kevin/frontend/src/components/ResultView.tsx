import { useMemo, useState } from "react";
import type { RunResult } from "../api/types";
import { CopyButton } from "./ui";
import { Search } from "./icons";

export default function ResultView({ r }: { r: RunResult }) {
  if (r.kind === "strings") return <StringsView text={String(r.result ?? "")} />;
  if (r.kind === "matches") return <MatchesView result={r.result as { matches: string[]; error?: string }} />;
  if (r.kind === "kv") return <KvView result={r.result as Record<string, string>} />;
  if (r.kind === "lines") return <CodeBlock text={(r.result as string[]).join("\n")} />;
  const txt = String(r.result ?? "");
  return txt ? <CodeBlock text={txt} /> : <Muted>Sin salida para este comando.</Muted>;
}

function Muted({ children }: { children: React.ReactNode }) {
  return <p className="text-sm text-slate-500">{children}</p>;
}

function CodeBlock({ text }: { text: string }) {
  return (
    <pre className="max-h-[480px] overflow-auto rounded-xl border border-line bg-ink-950/70 p-4 font-mono text-[12.5px] leading-relaxed text-slate-300">
      {text}
    </pre>
  );
}

function KvView({ result }: { result: Record<string, string> }) {
  const entries = Object.entries(result || {});
  if (!entries.length) return <Muted>Sin resultados para este comando.</Muted>;
  return (
    <ul className="divide-y divide-line">
      {entries.map(([k, v]) => (
        <li key={k} className="flex items-center gap-4 py-3">
          <span className="w-44 shrink-0 text-[13px] font-semibold text-slate-500">{k}</span>
          <span className="min-w-0 flex-1 break-all font-mono text-[13px] text-guinda-200">{v}</span>
          <CopyButton value={String(v)} label={`Copiar ${k}`} />
        </li>
      ))}
    </ul>
  );
}

function MatchesView({ result }: { result: { matches: string[]; error?: string } }) {
  const matches = result?.matches ?? [];
  if (!matches.length)
    return (
      <div className="flex items-center gap-2 text-sm text-ok">
        <span className="h-2 w-2 rounded-full bg-ok" />
        Sin coincidencias de reglas YARA.
      </div>
    );
  return (
    <div>
      <p className="mb-3 text-sm text-slate-400">
        {matches.length} regla{matches.length !== 1 ? "s" : ""} YARA coincide
        {matches.length !== 1 ? "n" : ""} con la muestra:
      </p>
      <div className="flex flex-wrap gap-2">
        {matches.map((m) => (
          <span
            key={m}
            className="inline-flex items-center gap-2 rounded-full border border-danger/40 bg-danger/10 px-3 py-1.5 font-mono text-xs text-rose-200"
          >
            <span className="h-1.5 w-1.5 rounded-full bg-danger" />
            {m}
          </span>
        ))}
      </div>
    </div>
  );
}

function StringsView({ text }: { text: string }) {
  const [q, setQ] = useState("");
  const lines = useMemo(() => text.split("\n").filter((l) => l.length), [text]);
  const filtered = useMemo(
    () => (q ? lines.filter((l) => l.toLowerCase().includes(q.toLowerCase())) : lines),
    [lines, q],
  );
  return (
    <div>
      <div className="mb-3 flex flex-wrap items-center gap-3">
        <div className="relative flex-1 min-w-[200px]">
          <Search
            width={16}
            height={16}
            className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-slate-500"
          />
          <input
            className="input pl-9"
            placeholder="Filtrar cadenas…"
            value={q}
            onChange={(e) => setQ(e.target.value)}
          />
        </div>
        <span className="text-sm text-slate-400">
          <strong className="text-white">{filtered.length}</strong> / {lines.length} cadenas
        </span>
      </div>
      <div className="max-h-[460px] overflow-auto rounded-xl border border-line bg-ink-950/70 py-2">
        {filtered.length === 0 ? (
          <p className="px-4 py-3 text-sm text-slate-500">Sin coincidencias.</p>
        ) : (
          <ol className="font-mono text-[12.5px]">
            {filtered.slice(0, 5000).map((l, i) => (
              <li key={i} className="flex gap-4 px-4 py-0.5 hover:bg-ink-800/60">
                <span className="w-10 shrink-0 select-none text-right text-slate-600">{i + 1}</span>
                <span className="whitespace-pre-wrap break-all text-slate-300">{l}</span>
              </li>
            ))}
          </ol>
        )}
      </div>
    </div>
  );
}
