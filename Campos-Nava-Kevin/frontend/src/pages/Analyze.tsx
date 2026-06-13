import { AnimatePresence, motion } from "framer-motion";
import { useEffect, useMemo, useState } from "react";
import { classify, getTools, runTool, uploadSample } from "../api/client";
import type {
  ExperimentResult,
  RunResult,
  SampleReport,
  Tool,
  ToolResult,
} from "../api/types";
import Dropzone from "../components/Dropzone";
import { Arrow, Bolt, Layers, Plus, Search, Shield, Terminal, Trash, X } from "../components/icons";
import ReportCard from "../components/ReportCard";
import { Alert, Page, PageHeader, Spinner } from "../components/ui";

type Mode = "default" | "all" | "custom";

interface Experiment {
  id: number;
  files: File[];
  mode: Mode;
  selected: string[];
  cmds: string[];
  cmdInput: string;
  minLen: number;
}

interface Progress {
  total: number;
  done: number;
  label: string;
}

let seq = 1;
const newExperiment = (): Experiment => ({
  id: seq++,
  files: [],
  mode: "default",
  selected: [],
  cmds: [],
  cmdInput: "",
  minLen: 4,
});

export default function Analyze() {
  const [tools, setTools] = useState<Tool[]>([]);
  const [toolsError, setToolsError] = useState(false);
  const [experiments, setExperiments] = useState<Experiment[]>([newExperiment()]);
  const [current, setCurrent] = useState(0); // experimento visible (paginación)
  const [progress, setProgress] = useState<Progress | null>(null);
  const [results, setResults] = useState<ExperimentResult[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getTools()
      .then(setTools)
      .catch(() => setToolsError(true));
  }, []);

  const defaults = useMemo(() => tools.filter((t) => t.por_defecto).map((t) => t.id), [tools]);

  const patch = (id: number, p: Partial<Experiment>) =>
    setExperiments((xs) => xs.map((e) => (e.id === id ? { ...e, ...p } : e)));

  const setCount = (n: number) => {
    const target = Math.max(1, Math.min(20, n));
    setExperiments((xs) => {
      if (target === xs.length) return xs;
      if (target < xs.length) return xs.slice(0, target);
      return [...xs, ...Array.from({ length: target - xs.length }, newExperiment)];
    });
    setCurrent((c) => Math.min(c, target - 1));
  };

  const addExperiment = () => {
    setExperiments((xs) => [...xs, newExperiment()]);
    setCurrent(experiments.length); // navega al recién creado (último)
  };

  const removeExperiment = (id: number) => {
    setExperiments((xs) => xs.filter((x) => x.id !== id));
    setCurrent((c) => Math.max(0, Math.min(c, experiments.length - 2)));
  };

  const toolsFor = (e: Experiment): string[] => {
    if (e.mode === "all") return tools.map((t) => t.id);
    if (e.mode === "custom") return e.selected;
    return defaults;
  };

  const totalSamples = experiments.reduce((a, e) => a + e.files.length, 0);

  async function run() {
    setError(null);
    if (totalSamples === 0) {
      setError("Añade al menos una muestra a algún experimento.");
      return;
    }

    // Plan de trabajo total para la barra de progreso.
    let total = 0;
    for (const e of experiments) {
      const t = toolsFor(e).length + e.cmds.length;
      total += e.files.length * Math.max(1, t);
    }
    setProgress({ total, done: 0, label: "Preparando…" });
    let done = 0;
    const bump = (label: string) => setProgress({ total, done: ++done, label });

    const labelOf = (id: string) => tools.find((t) => t.id === id)?.etiqueta ?? id;
    const out: ExperimentResult[] = [];

    try {
      let n = 0;
      for (const e of experiments) {
        n++;
        if (!e.files.length) continue;
        const toolIds = toolsFor(e);
        const reports: SampleReport[] = [];
        const errors: { filename: string; error: string }[] = [];

        for (const file of e.files) {
          try {
            setProgress({ total, done, label: `Subiendo ${file.name}…` });
            const meta = await uploadSample(file);
            const resultados: RunResult[] = [];

            for (const tid of toolIds) {
              setProgress({ total, done, label: `Exp ${n} · ${file.name} · ${labelOf(tid)}` });
              const result = await runTool(meta.sha256, tid, { min_len: e.minLen });
              resultados.push({ id: tid, etiqueta: labelOf(tid), kind: classify(tid, result), result });
              bump(`Exp ${n} · ${labelOf(tid)} ✓`);
            }
            for (const cmd of e.cmds) {
              setProgress({ total, done, label: `Exp ${n} · ${file.name} · $ ${cmd}` });
              const result = await runTool(meta.sha256, "custom", { cmd });
              resultados.push({ id: "custom", etiqueta: `$ ${cmd}`, kind: classify("custom", result), result });
              bump(`Exp ${n} · ${cmd} ✓`);
            }

            const mapa: Record<string, ToolResult> = {};
            for (const r of resultados) if (r.id !== "custom") mapa[r.id] = r.result;
            reports.push({ sha256: meta.sha256, filename: meta.filename, size: meta.size, resultados, mapa });
          } catch (err) {
            errors.push({ filename: file.name, error: String((err as Error).message ?? err) });
          }
        }
        out.push({ numero: n, reports, errors });
      }
      setResults(out);
    } catch (err) {
      setError(String((err as Error).message ?? err));
    } finally {
      setProgress(null);
    }
  }

  function reset() {
    seq = 1;
    setResults(null);
    setExperiments([newExperiment()]);
    setCurrent(0);
    setError(null);
  }

  if (results) return <Results experiments={results} onReset={reset} />;

  const idx = Math.min(current, experiments.length - 1);
  const exp = experiments[idx];

  return (
    <Page>
      <Hero />

      {error && <Alert title="No se pudo analizar">{error}</Alert>}
      {toolsError && (
        <Alert tone="warn" title="Catálogo no disponible">
          No se pudo leer el catálogo de comandos del motor. ¿Está corriendo el engine en :8001?
        </Alert>
      )}

      <div className="mb-5 flex flex-wrap items-center justify-between gap-3 rounded-xl border border-line bg-ink-900/60 px-4 py-3">
        <div className="flex items-center gap-3">
          <Layers width={18} height={18} className="text-guinda-300" />
          <span className="text-sm font-medium text-slate-300">¿Cuántos experimentos?</span>
        </div>
        <Stepper value={experiments.length} onChange={setCount} />
      </div>

      {experiments.length > 1 && (
        <Pager current={idx} total={experiments.length} onSelect={setCurrent} />
      )}

      <div className="relative">
        <AnimatePresence mode="wait" initial={false}>
          <ExperimentCard
            key={exp.id}
            index={idx}
            exp={exp}
            tools={tools}
            canRemove={experiments.length > 1}
            onPatch={(p) => patch(exp.id, p)}
            onRemove={() => removeExperiment(exp.id)}
          />
        </AnimatePresence>
      </div>

      <button type="button" onClick={addExperiment} className="btn-ghost mt-4 w-full">
        <Plus width={18} height={18} /> Añadir otro experimento
      </button>

      <button
        type="button"
        onClick={run}
        disabled={!!progress}
        className="btn-primary mt-4 w-full py-3 text-base"
      >
        {progress ? <Spinner className="h-5 w-5" /> : <Search width={18} height={18} />}
        {progress
          ? "Analizando…"
          : `Analizar ${totalSamples || ""} muestra${totalSamples === 1 ? "" : "s"}`.trim()}
      </button>

      <Features />

      <AnimatePresence>{progress && <ProgressOverlay p={progress} />}</AnimatePresence>
    </Page>
  );
}

/* ---------- Hero ---------- */
function Hero() {
  return (
    <section className="relative mb-10 overflow-hidden rounded-3xl border border-line bg-ink-900/50 px-7 py-12 md:px-12 md:py-16">
      <div className="grid-bg absolute inset-0 animate-grid-pan opacity-60" />
      <div className="absolute -right-16 -top-16 h-64 w-64 rounded-full bg-guinda-700/20 blur-3xl" />
      <div className="relative">
        <span className="eyebrow inline-flex items-center gap-2 rounded-full border border-guinda-500/30 bg-guinda-700/20 px-3 py-1">
          <Shield width={14} height={14} /> Análisis estático · sandbox aislado
        </span>
        <h1 className="mt-5 max-w-2xl font-display text-4xl font-extrabold leading-tight tracking-tight text-white md:text-5xl">
          Inspecciona binarios <span className="text-gradient">sin ejecutarlos</span>
        </h1>
        <p className="mt-4 max-w-2xl text-slate-400 md:text-lg">
          Arma uno o varios <strong className="text-slate-200">experimentos</strong>: cada uno con
          sus propias muestras y comandos (hashes, entropía, cadenas, metadatos, cabeceras ELF,
          YARA, radare2…). Todo corre en un contenedor sin acceso a la red.
        </p>
      </div>
    </section>
  );
}

/* ---------- Stepper de número de experimentos ---------- */
function Stepper({ value, onChange }: { value: number; onChange: (n: number) => void }) {
  return (
    <div className="flex items-center gap-1 rounded-lg border border-line-strong bg-ink-950/60 p-1">
      <button
        className="grid h-8 w-8 place-items-center rounded-md text-slate-300 hover:bg-ink-700 hover:text-white"
        onClick={() => onChange(value - 1)}
        aria-label="Menos experimentos"
      >
        −
      </button>
      <input
        type="number"
        min={1}
        max={20}
        value={value}
        onChange={(e) => onChange(parseInt(e.target.value || "1", 10))}
        className="w-12 bg-transparent text-center font-mono text-sm text-white outline-none"
      />
      <button
        className="grid h-8 w-8 place-items-center rounded-md text-slate-300 hover:bg-ink-700 hover:text-white"
        onClick={() => onChange(value + 1)}
        aria-label="Más experimentos"
      >
        +
      </button>
    </div>
  );
}

/* ---------- Paginación de experimentos (uno por pantalla) ---------- */
function Pager({
  current,
  total,
  onSelect,
}: {
  current: number;
  total: number;
  onSelect: (n: number) => void;
}) {
  return (
    <div className="mb-4 flex items-center justify-between gap-3 rounded-xl border border-line bg-ink-900/60 px-3 py-2">
      <button
        onClick={() => onSelect(Math.max(0, current - 1))}
        disabled={current === 0}
        className="btn-ghost px-3 py-1.5 text-xs"
      >
        <Arrow width={15} height={15} className="rotate-180" /> Anterior
      </button>
      <div className="flex items-center gap-1.5 overflow-x-auto">
        {Array.from({ length: total }).map((_, i) => (
          <button
            key={i}
            onClick={() => onSelect(i)}
            aria-label={`Ver experimento ${i + 1}`}
            aria-current={i === current}
            className={`grid h-8 w-8 shrink-0 place-items-center rounded-lg text-xs font-bold transition ${
              i === current
                ? "bg-guinda-600 text-white shadow-glow"
                : "border border-line text-slate-400 hover:bg-ink-800 hover:text-white"
            }`}
          >
            {i + 1}
          </button>
        ))}
      </div>
      <button
        onClick={() => onSelect(Math.min(total - 1, current + 1))}
        disabled={current === total - 1}
        className="btn-ghost px-3 py-1.5 text-xs"
      >
        Siguiente <Arrow width={15} height={15} />
      </button>
    </div>
  );
}

/* ---------- Tarjeta de un experimento ---------- */
function ExperimentCard({
  index,
  exp,
  tools,
  canRemove,
  onPatch,
  onRemove,
}: {
  index: number;
  exp: Experiment;
  tools: Tool[];
  canRemove: boolean;
  onPatch: (p: Partial<Experiment>) => void;
  onRemove: () => void;
}) {
  const modes: { id: Mode; name: string; desc: string; icon: typeof Bolt }[] = [
    { id: "default", name: "Por defecto", desc: "Hashes, tipo, entropía, metadatos, ELF y YARA.", icon: Shield },
    { id: "all", name: "Todos los comandos", desc: "Ejecuta el catálogo completo sobre cada muestra.", icon: Bolt },
    { id: "custom", name: "Personalizado", desc: "Elige exactamente qué comandos correr.", icon: Terminal },
  ];

  const toggle = (id: string) =>
    onPatch({
      selected: exp.selected.includes(id)
        ? exp.selected.filter((x) => x !== id)
        : [...exp.selected, id],
    });

  const addCmd = () => {
    const v = exp.cmdInput.trim();
    if (v) onPatch({ cmds: [...exp.cmds, v], cmdInput: "" });
  };

  return (
    <motion.section
      layout
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, scale: 0.97 }}
      transition={{ duration: 0.3, ease: [0.22, 1, 0.36, 1] }}
      className="card card-hover p-5 md:p-6"
    >
      <header className="mb-4 flex items-center justify-between">
        <span className="inline-flex items-center gap-2 rounded-full bg-guinda-700/25 px-3 py-1 text-xs font-bold uppercase tracking-wider text-guinda-200">
          <span className="grid h-5 w-5 place-items-center rounded-full bg-guinda-600 text-white">
            {index + 1}
          </span>
          Experimento {index + 1}
        </span>
        {canRemove && (
          <button
            onClick={onRemove}
            className="grid h-8 w-8 place-items-center rounded-md border border-line text-slate-500 hover:border-danger hover:text-danger"
            aria-label="Quitar experimento"
          >
            <Trash width={15} height={15} />
          </button>
        )}
      </header>

      <Dropzone files={exp.files} onChange={(files) => onPatch({ files })} />

      <p className="label mt-5 mb-2">Tipo de análisis</p>
      <div className="grid gap-3 sm:grid-cols-3">
        {modes.map((m) => {
          const Icon = m.icon;
          const active = exp.mode === m.id;
          return (
            <button
              key={m.id}
              onClick={() => onPatch({ mode: m.id })}
              className={`flex flex-col items-start gap-1.5 rounded-xl border p-3.5 text-left transition ${
                active
                  ? "border-guinda-500 bg-guinda-700/20"
                  : "border-line bg-ink-950/40 hover:border-line-strong"
              }`}
            >
              <Icon width={18} height={18} className={active ? "text-guinda-300" : "text-slate-400"} />
              <span className="text-sm font-semibold text-white">{m.name}</span>
              <span className="text-xs leading-snug text-slate-400">{m.desc}</span>
            </button>
          );
        })}
      </div>

      <AnimatePresence initial={false}>
        {exp.mode === "custom" && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.25 }}
            className="overflow-hidden"
          >
            <div className="mt-4 rounded-xl border border-line bg-ink-950/40 p-4">
              <p className="label mb-3">Comandos disponibles</p>
              {tools.length === 0 ? (
                <p className="text-sm text-slate-500">Catálogo no disponible.</p>
              ) : (
                <div className="grid gap-2 sm:grid-cols-2">
                  {tools.map((t) => {
                    const on = exp.selected.includes(t.id);
                    return (
                      <label
                        key={t.id}
                        className={`flex cursor-pointer items-center gap-3 rounded-lg border px-3 py-2 transition ${
                          on ? "border-guinda-500/60 bg-guinda-700/15" : "border-line hover:border-line-strong"
                        }`}
                      >
                        <input
                          type="checkbox"
                          checked={on}
                          onChange={() => toggle(t.id)}
                          className="h-4 w-4 accent-guinda-500"
                        />
                        <span className="flex-1 text-sm text-slate-200">{t.etiqueta}</span>
                        {t.por_defecto && (
                          <span className="rounded-full bg-guinda-700/30 px-2 py-0.5 text-[10px] font-bold uppercase text-guinda-200">
                            def
                          </span>
                        )}
                      </label>
                    );
                  })}
                </div>
              )}

              <div className="mt-4 flex items-center gap-2">
                <label className="text-sm text-slate-400">Longitud mín. (strings)</label>
                <input
                  type="number"
                  min={1}
                  max={100}
                  value={exp.minLen}
                  onChange={(e) => onPatch({ minLen: parseInt(e.target.value || "4", 10) })}
                  className="input w-20"
                />
              </div>

              <p className="label mb-2 mt-5">Añade un comando guiado</p>
              <div className="flex items-center gap-2 rounded-lg border border-line-strong bg-ink-950/60 px-3 focus-within:border-guinda-400">
                <Terminal width={16} height={16} className="text-slate-500" />
                <input
                  className="flex-1 bg-transparent py-2.5 font-mono text-[13px] text-slate-100 outline-none placeholder:text-slate-600"
                  placeholder="objdump -d  ·  nm -D  ·  strings -n 10  — Enter para añadir"
                  value={exp.cmdInput}
                  onChange={(e) => onPatch({ cmdInput: e.target.value })}
                  onKeyDown={(e) => {
                    if (e.key === "Enter") {
                      e.preventDefault();
                      addCmd();
                    }
                  }}
                />
                <button onClick={addCmd} className="btn-primary px-3 py-1.5 text-xs">
                  Añadir
                </button>
              </div>
              {exp.cmds.length > 0 && (
                <ul className="mt-3 flex flex-wrap gap-2">
                  {exp.cmds.map((c, i) => (
                    <li key={i} className="chip font-mono text-guinda-200">
                      {c}
                      <button
                        onClick={() => onPatch({ cmds: exp.cmds.filter((_, idx) => idx !== i) })}
                        className="text-slate-500 hover:text-danger"
                        aria-label="Quitar comando"
                      >
                        <X width={13} height={13} />
                      </button>
                    </li>
                  ))}
                </ul>
              )}
              <p className="mt-3 text-xs text-slate-500">
                Cada comando corre en el sandbox aislado; solo si el binario está en la whitelist
                del backend (objdump, readelf, nm, strings, r2…), sin encadenar con ; | &amp;.
              </p>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.section>
  );
}

/* ---------- Overlay de progreso ---------- */
function ProgressOverlay({ p }: { p: Progress }) {
  const pct = p.total ? Math.round((p.done / p.total) * 100) : 0;
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 z-50 grid place-items-center bg-ink-950/85 backdrop-blur-md"
    >
      <div className="card w-[min(420px,90vw)] p-8 text-center">
        <div className="relative mx-auto mb-5 h-16 w-16">
          <span className="absolute inset-0 animate-spin rounded-full border-[3px] border-ink-700 border-t-guinda-400" />
          <span className="absolute inset-0 grid place-items-center font-mono text-sm font-bold text-white">
            {pct}%
          </span>
        </div>
        <h3 className="text-base font-semibold text-white">Analizando muestras</h3>
        <p className="mt-1 h-5 truncate font-mono text-xs text-slate-400">{p.label}</p>
        <div className="mt-4 h-2 w-full overflow-hidden rounded-full bg-ink-700">
          <motion.div
            className="h-full rounded-full bg-gradient-to-r from-guinda-500 to-oro-400"
            animate={{ width: `${pct}%` }}
            transition={{ duration: 0.3 }}
          />
        </div>
        <p className="mt-2 text-xs text-slate-500">
          {p.done} / {p.total} tareas
        </p>
      </div>
    </motion.div>
  );
}

/* ---------- Resultados ---------- */
function Results({
  experiments,
  onReset,
}: {
  experiments: ExperimentResult[];
  onReset: () => void;
}) {
  return (
    <Page>
      <PageHeader
        eyebrow="Reporte de análisis"
        title={`${experiments.length} experimento${experiments.length === 1 ? "" : "s"}`}
        right={
          <button onClick={onReset} className="btn-ghost">
            <Search width={16} height={16} /> Analizar otras
          </button>
        }
      />
      <div className="space-y-12">
        {experiments.map((exp) => (
          <section key={exp.numero}>
            <header className="mb-5 border-b border-line pb-3">
              <p className="eyebrow">Experimento {exp.numero}</p>
              <h2 className="mt-1 font-display text-xl font-bold text-white">
                {exp.reports.length} muestra{exp.reports.length === 1 ? "" : "s"} analizada
                {exp.reports.length === 1 ? "" : "s"}
              </h2>
            </header>
            {exp.errors.length > 0 && (
              <Alert title="Algunas muestras fallaron">
                <ul className="list-disc pl-5">
                  {exp.errors.map((e, i) => (
                    <li key={i}>
                      {e.filename}: {e.error}
                    </li>
                  ))}
                </ul>
              </Alert>
            )}
            <div className="space-y-5">
              {exp.reports.map((r, i) => (
                <ReportCard key={r.sha256 + i} report={r} index={i} total={exp.reports.length} />
              ))}
            </div>
          </section>
        ))}
      </div>
    </Page>
  );
}

/* ---------- Tarjetas de características ---------- */
function Features() {
  const items = [
    { icon: Shield, title: "Sandbox aislado", text: "Sin red ni acceso al host; las muestras nunca se ejecutan." },
    { icon: Layers, title: "Por lotes", text: "Varios experimentos, cada uno con N muestras y sus comandos." },
    { icon: Bolt, title: "Catálogo completo", text: "Hashes, entropía, YARA, ELF, radare2, strings, xxd y más." },
  ];
  return (
    <div className="mt-10 grid gap-4 sm:grid-cols-3">
      {items.map((f) => {
        const Icon = f.icon;
        return (
          <div key={f.title} className="card p-5">
            <div className="mb-3 grid h-10 w-10 place-items-center rounded-lg bg-ink-800 text-guinda-300">
              <Icon width={19} height={19} />
            </div>
            <h3 className="font-semibold text-white">{f.title}</h3>
            <p className="mt-1 text-sm text-slate-400">{f.text}</p>
          </div>
        );
      })}
    </div>
  );
}
