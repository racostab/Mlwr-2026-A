import { motion } from "framer-motion";
import { useEffect, useMemo, useState } from "react";
import { getSamples } from "../api/client";
import type { SampleRow } from "../api/types";
import { Clock, Search } from "../components/icons";
import { Alert, CopyButton, EmptyState, Page, PageHeader, Skeleton } from "../components/ui";
import { fmtDate, humanSize, shortSha } from "../lib/format";

export default function History() {
  const [samples, setSamples] = useState<SampleRow[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [q, setQ] = useState("");

  useEffect(() => {
    getSamples()
      .then(setSamples)
      .catch((e) => setError(String(e.message ?? e)));
  }, []);

  const filtered = useMemo(
    () =>
      (samples ?? []).filter(
        (s) =>
          !q ||
          s.filename.toLowerCase().includes(q.toLowerCase()) ||
          s.sha256.includes(q.toLowerCase()),
      ),
    [samples, q],
  );

  return (
    <Page>
      <PageHeader
        eyebrow="Análisis"
        title="Historial de muestras"
        right={
          samples ? (
            <span className="chip text-guinda-200">{samples.length} muestras</span>
          ) : undefined
        }
      />

      {error && <Alert title="No se pudo cargar el historial">{error}</Alert>}

      {samples === null ? (
        <div className="space-y-2">
          {Array.from({ length: 6 }).map((_, i) => (
            <Skeleton key={i} className="h-14 w-full" />
          ))}
        </div>
      ) : samples.length === 0 ? (
        <EmptyState icon={<Clock width={28} height={28} />} title="Sin muestras todavía"
          text="Las muestras que analices aparecerán aquí, nombradas por su SHA-256." />
      ) : (
        <>
          <div className="relative mb-4 max-w-md">
            <Search width={16} height={16} className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
            <input className="input pl-9" placeholder="Buscar por nombre o hash…" value={q}
              onChange={(e) => setQ(e.target.value)} />
          </div>
          <div className="card overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-line text-left text-[11px] uppercase tracking-wider text-slate-500">
                    <th className="px-5 py-3.5 font-semibold">Muestra</th>
                    <th className="px-5 py-3.5 font-semibold">SHA-256</th>
                    <th className="px-5 py-3.5 font-semibold">Tamaño</th>
                    <th className="px-5 py-3.5 font-semibold">Subida</th>
                  </tr>
                </thead>
                <tbody>
                  {filtered.map((s, i) => (
                    <motion.tr
                      key={s.sha256}
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      transition={{ delay: Math.min(i * 0.02, 0.3) }}
                      className="border-b border-line/70 last:border-0 hover:bg-ink-800/40"
                    >
                      <td className="px-5 py-3.5 font-medium text-slate-200">{s.filename}</td>
                      <td className="px-5 py-3.5">
                        <span className="inline-flex items-center gap-2">
                          <span className="font-mono text-xs text-guinda-200" title={s.sha256}>
                            {shortSha(s.sha256, 16)}
                          </span>
                          <CopyButton value={s.sha256} label="Copiar SHA-256" />
                        </span>
                      </td>
                      <td className="px-5 py-3.5 text-slate-400">{humanSize(s.size)}</td>
                      <td className="px-5 py-3.5 text-slate-500">{fmtDate(s.uploaded_at)}</td>
                    </motion.tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}
    </Page>
  );
}
