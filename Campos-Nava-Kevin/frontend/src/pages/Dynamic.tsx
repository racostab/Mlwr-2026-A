import { AnimatePresence, motion } from "framer-motion";
import { useEffect, useRef, useState } from "react";
import { createDynamicJob, dynamicFileUrl, getDynamicState, listDynamicJobs } from "../api/client";
import type { DynamicJob, DynamicState, VolcadoAnalisis } from "../api/types";
import { Arrow, FileBinary, Target, Terminal, Upload } from "../components/icons";
import { Alert, Page, PageHeader, Spinner, StatusDot } from "../components/ui";
import { fmtDate } from "../lib/format";

const ACTIVE = new Set(["en_cola", "ejecutando", "analizando_volcado"]);

export default function Dynamic() {
  const [state, setState] = useState<DynamicState | null>(null);
  const [jobs, setJobs] = useState<DynamicJob[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [file, setFile] = useState<File | null>(null);
  const MIN_SEGUNDOS = 26;
  const [segundos, setSegundos] = useState(String(MIN_SEGUNDOS));
  const [sending, setSending] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const refresh = async () => {
    try {
      const [s, j] = await Promise.all([getDynamicState(), listDynamicJobs()]);
      setState(s);
      setJobs(j);
      setError(null);
    } catch {
      setError(
        "Servicio dinámico no disponible. Arráncalo en el host con: bash dinamico/scripts/servicio_dinamico.sh",
      );
    }
  };

  useEffect(() => {
    refresh();
    const id = setInterval(refresh, 4000);
    return () => clearInterval(id);
  }, []);

  const hasActive = jobs.some((j) => ACTIVE.has(j.estado));

  async function submit() {
    if (!file) return;
    const s = Math.max(MIN_SEGUNDOS, parseInt(segundos || "0", 10) || MIN_SEGUNDOS);
    if (s !== parseInt(segundos, 10)) setSegundos(String(s));
    setSending(true);
    setError(null);
    try {
      await createDynamicJob(file, s);
      setFile(null);
      if (inputRef.current) inputRef.current.value = "";
      await refresh();
    } catch (e) {
      setError(`No se pudo encolar la detonación: ${(e as Error).message ?? e}`);
    } finally {
      setSending(false);
    }
  }

  return (
    <Page>
      <PageHeader
        eyebrow="Laboratorio"
        title="Análisis dinámico"
        lead="La muestra se detona dentro de una VM Kali aislada (red host-only, sin NAT, firewall del host). Antes de ejecutar nada se restaura un estado limpio y se verifica la jaula; si hay fuga, se aborta sin detonar."
        right={
          state && state.en_cola > 0 ? (
            <span className="chip text-guinda-200">{state.en_cola} en cola</span>
          ) : undefined
        }
      />

      {error && <Alert title="Servicio dinámico">{error}</Alert>}

      <div className="grid gap-5 lg:grid-cols-[1fr_1.1fr]">
        {/* Readiness de la jaula */}
        <div className="card p-5 md:p-6">
          <h2 className="mb-4 flex items-center gap-2 font-display text-base font-bold text-white">
            <Target width={18} height={18} className="text-guinda-300" /> Estado de la jaula
          </h2>
          <ul className="space-y-1">
            <Row label="VirtualBox (host)" ok={!!state?.vbox_disponible}
              text={state?.vbox_disponible ? "disponible" : "no instalado"} />
            <Row label={`VM «${state?.vm ?? "kali"}»`} ok={!!state?.vm_existe}
              text={state?.vm_existe ? "existe" : "no creada (vagrant up)"} />
            <Row label="Snapshot limpio" ok={!!state?.snapshot_limpio}
              text={state?.snapshot_limpio ? "presente" : "falta — créalo"} />
            <Row label="Estado de la VM" ok={!!state?.vm_corriendo} neutral
              text={state?.vm_corriendo ? "encendida" : "apagada"} />
          </ul>
        </div>

        {/* Detonar */}
        <div className="card p-5 md:p-6">
          <h2 className="mb-4 flex items-center gap-2 font-display text-base font-bold text-white">
            <Terminal width={18} height={18} className="text-guinda-300" /> Detonar una muestra
          </h2>
          <label
            className={`flex cursor-pointer items-center gap-3 rounded-xl border-2 border-dashed px-4 py-5 transition ${
              file ? "border-ok/50 bg-ok/5" : "border-line-strong hover:border-guinda-500"
            }`}
          >
            <span className={`grid h-11 w-11 place-items-center rounded-full ${file ? "bg-ok/15 text-ok" : "bg-guinda-700/20 text-guinda-300"}`}>
              {file ? <FileBinary width={20} height={20} /> : <Upload width={20} height={20} />}
            </span>
            <span className="min-w-0">
              <span className="block truncate text-sm font-semibold text-white">
                {file ? file.name : "Selecciona un binario ELF"}
              </span>
              <span className="block text-xs text-slate-400">
                {file ? "Listo para detonar" : "una muestra por detonación"}
              </span>
            </span>
            <input
              ref={inputRef}
              type="file"
              className="hidden"
              onChange={(e) => setFile(e.target.files?.[0] ?? null)}
            />
          </label>

          <div className="mt-4 flex items-end gap-3">
            <label className="flex-1">
              <span className="label mb-1 block">Tiempo de ejecución (s)</span>
              <input
                type="number"
                min={MIN_SEGUNDOS}
                max={120}
                value={segundos}
                onChange={(e) => setSegundos(e.target.value)}
                onBlur={() => {
                  const n = parseInt(segundos, 10);
                  if (!segundos || isNaN(n) || n < MIN_SEGUNDOS) setSegundos(String(MIN_SEGUNDOS));
                }}
                className="input"
              />
            </label>
            <button
              onClick={submit}
              disabled={!file || sending || !state?.vm_existe}
              className="btn-primary px-5 py-2.5"
              title={!state?.vm_existe ? "La VM no existe todavía" : undefined}
            >
              {sending ? <Spinner className="h-4 w-4" /> : <Terminal width={16} height={16} />}
              Comenzar
            </button>
          </div>
          <p className="mt-3 text-xs text-slate-500">
            Resultados en el host, en <code className="font-mono text-slate-400">dynamic_output/&lt;ts&gt;/</code>:
            strace.log (syscalls), stdout/stderr y el volcado de memoria.
          </p>
        </div>
      </div>

      {/* Jobs */}
      <div className="mt-6">
        <div className="mb-3 flex items-center justify-between">
          <h2 className="font-display text-lg font-bold text-white">Detonaciones recientes</h2>
          {hasActive && (
            <span className="flex items-center gap-2 text-xs text-guinda-200">
              <Spinner className="h-3.5 w-3.5" /> actualizando…
            </span>
          )}
        </div>
        {jobs.length === 0 ? (
          <div className="card px-6 py-12 text-center text-sm text-slate-500">
            Aún no hay detonaciones. Sube una muestra para empezar.
          </div>
        ) : (
          <div className="space-y-3">
            <AnimatePresence initial={false}>
              {jobs.map((j) => (
                <JobCard key={j.id} job={j} />
              ))}
            </AnimatePresence>
          </div>
        )}
      </div>
    </Page>
  );
}

function Row({
  label,
  text,
  ok,
  neutral,
}: {
  label: string;
  text: string;
  ok: boolean;
  neutral?: boolean;
}) {
  return (
    <li className="flex items-center justify-between gap-3 border-b border-line py-2.5 last:border-0">
      <span className="text-sm text-slate-400">{label}</span>
      <span className="flex items-center gap-2 text-sm font-medium text-slate-200">
        {!neutral && <StatusDot ok={ok} />}
        {text}
      </span>
    </li>
  );
}

const STATE_META: Record<string, { text: string; cls: string }> = {
  listo: { text: "✓ listo", cls: "border-ok/40 bg-ok/10 text-ok" },
  error: { text: "✗ error", cls: "border-danger/40 bg-danger/10 text-danger" },
  ejecutando: { text: "● detonando…", cls: "border-guinda-500/40 bg-guinda-700/20 text-guinda-200" },
  analizando_volcado: { text: "● escaneando volcado…", cls: "border-oro-400/40 bg-oro-500/10 text-oro-300" },
  en_cola: { text: "… en cola", cls: "border-line bg-ink-800 text-slate-400" },
};

function JobCard({ job }: { job: DynamicJob }) {
  const meta = STATE_META[job.estado] ?? STATE_META.en_cola;
  // Cronómetro en vivo mientras la muestra corre: en vez de un texto fijo
  // ("detonando…") mostramos los segundos transcurridos.
  const corriendo = job.estado === "ejecutando";
  const [ahora, setAhora] = useState(() => Date.now());
  useEffect(() => {
    if (!corriendo) return;
    const id = setInterval(() => setAhora(Date.now()), 1000);
    return () => clearInterval(id);
  }, [corriendo]);
  const transcurridos = Math.max(0, Math.floor((ahora - Date.parse(job.creado)) / 1000));
  const textoEstado = corriendo ? `● ${transcurridos}s detonando` : meta.text;
  const tecnicas = job.mitre?.tecnicas ?? [];
  const post = job.post_analisis ?? {};
  // Entradas de volcado con resultados reales (se omite la clave "_aviso").
  const volcados = Object.entries(post).filter(
    ([k, v]) => !k.startsWith("_") && typeof v === "object" && v !== null,
  ) as [string, VolcadoAnalisis][];
  const aviso = typeof post["_aviso"] === "string" ? (post["_aviso"] as string) : null;

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0 }}
      className="card p-4 md:p-5"
    >
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <FileBinary width={18} height={18} className="text-guinda-300" />
          <span className="font-mono text-sm text-slate-200">{job.filename}</span>
        </div>
        <span className={`rounded-full border px-3 py-1 text-xs font-semibold ${meta.cls}`}>
          {textoEstado}
        </span>
      </div>

      <div className="mt-2 flex flex-wrap items-center gap-x-5 gap-y-1 text-xs text-slate-500">
        <span>{job.segundos}s de ejecución</span>
        <span>{fmtDate(job.creado)}</span>
        {job.destino && <span className="font-mono text-slate-400">{job.destino}</span>}
      </div>

      {job.estado === "error" && job.error && (
        <p className="mt-3 rounded-lg border border-danger/30 bg-danger/10 px-3 py-2 font-mono text-xs text-rose-200">
          {job.error}
        </p>
      )}

      {/* Archivos de resultados: descargables (strace.log, post_analisis.json,
          stdout/stderr.log, volcado de memoria…). */}
      {job.archivos?.length > 0 && (
        <div className="mt-3">
          <p className="mb-2 text-xs font-bold uppercase tracking-wider text-slate-500">
            Archivos de resultados
          </p>
          <div className="flex flex-wrap gap-1.5">
            {job.archivos.map((a) => (
              <a
                key={a}
                href={dynamicFileUrl(job.id, a)}
                download
                className="flex items-center gap-1.5 rounded-md border border-line bg-ink-800 px-2 py-1 font-mono text-[11px] text-slate-300 transition-colors hover:border-guinda-500/40 hover:text-guinda-200"
              >
                <Arrow width={12} height={12} className="rotate-90" />
                {a}
              </a>
            ))}
          </div>
        </div>
      )}

      {/* Hallazgos del volcado de memoria (YARA + strings del post-análisis). */}
      {volcados.length > 0 && (
        <div className="mt-4 border-t border-line pt-3">
          <p className="mb-2 text-xs font-bold uppercase tracking-wider text-slate-500">
            Hallazgos del volcado de memoria
          </p>
          <div className="space-y-3">
            {volcados.map(([nombre, v]) => (
              <VolcadoHallazgos key={nombre} nombre={nombre} v={v} />
            ))}
          </div>
        </div>
      )}
      {aviso && volcados.length === 0 && (
        <p className="mt-3 text-xs text-slate-500">{aviso}</p>
      )}

      {tecnicas.length > 0 && (
        <div className="mt-4 border-t border-line pt-3">
          <p className="mb-2 flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-slate-500">
            <Target width={14} height={14} /> {tecnicas.length} técnica
            {tecnicas.length === 1 ? "" : "s"} MITRE ATT&CK
          </p>
          <div className="space-y-1.5">
            {tecnicas.map((t) => (
              <details
                key={t.id}
                className="rounded-lg border border-guinda-500/25 bg-guinda-700/10 px-3 py-2"
              >
                <summary className="flex cursor-pointer flex-wrap items-center justify-between gap-2">
                  <span className="font-mono text-[11px] text-guinda-200">
                    {t.id} · {t.nombre}
                  </span>
                  <span className="text-[10px] uppercase tracking-wider text-slate-500">
                    {t.tactica_es}
                  </span>
                </summary>
                {t.evidencia?.length > 0 && (
                  <ul className="mt-2 space-y-0.5 border-t border-guinda-500/15 pt-2">
                    {t.evidencia.map((e, i) => (
                      <li key={i} className="break-all font-mono text-[11px] text-slate-400">
                        {e}
                      </li>
                    ))}
                  </ul>
                )}
              </details>
            ))}
          </div>
        </div>
      )}
    </motion.div>
  );
}

// Muestra lo que el motor estático extrajo de un volcado: coincidencias YARA
// (lo más jugoso: C2/packing/anti-VM) y las `strings` en claro (colapsadas).
function VolcadoHallazgos({ nombre, v }: { nombre: string; v: VolcadoAnalisis }) {
  const matches = v.yara?.matches ?? [];
  const lineas = v.strings ? v.strings.split("\n") : [];
  const TOPE = 500; // las strings de un volcado pueden ser enormes; recortamos.
  return (
    <div className="rounded-lg border border-line bg-ink-900/40 p-3">
      <p className="font-mono text-[11px] text-slate-300">{nombre}</p>
      {v.error ? (
        <p className="mt-1 font-mono text-[11px] text-rose-300">{v.error}</p>
      ) : (
        <>
          <div className="mt-2 flex flex-wrap items-center gap-1.5">
            <span className="text-[11px] text-slate-500">YARA:</span>
            {matches.length > 0 ? (
              matches.map((m) => (
                <span
                  key={m}
                  className="rounded border border-oro-400/30 bg-oro-500/10 px-1.5 py-0.5 font-mono text-[11px] text-oro-300"
                >
                  {m}
                </span>
              ))
            ) : (
              <span className="text-[11px] text-slate-400">sin coincidencias</span>
            )}
          </div>
          {lineas.length > 0 && (
            <details className="mt-2">
              <summary className="cursor-pointer text-[11px] text-slate-500">
                strings — {lineas.length} líneas
                {lineas.length > TOPE ? ` (se muestran ${TOPE}; descarga el archivo para todas)` : ""}
              </summary>
              <pre className="mt-2 max-h-60 overflow-auto rounded bg-ink-950 p-2 font-mono text-[11px] text-slate-400">
                {lineas.slice(0, TOPE).join("\n")}
              </pre>
            </details>
          )}
          {v.radare_dump && (
            <details className="mt-2">
              <summary className="cursor-pointer text-[11px] text-slate-500">
                radare2 — desensamblado del volcado (info · segmentos · registros · disasm @ RIP)
              </summary>
              <pre className="mt-2 max-h-60 overflow-auto rounded bg-ink-950 p-2 font-mono text-[11px] text-slate-400">
                {v.radare_dump}
              </pre>
            </details>
          )}
        </>
      )}
    </div>
  );
}
