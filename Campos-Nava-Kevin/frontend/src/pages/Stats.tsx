import { motion } from "framer-motion";
import { useEffect, useState } from "react";
import { getStats } from "../api/client";
import type { Stats as StatsT } from "../api/types";
import { Chart } from "../components/icons";
import { Alert, EmptyState, Page, PageHeader, Skeleton } from "../components/ui";
import { fmtDate, humanSize, shortSha } from "../lib/format";

export default function Stats() {
  const [stats, setStats] = useState<StatsT | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getStats()
      .then(setStats)
      .catch((e) => setError(String(e.message ?? e)));
  }, []);

  if (error) return <Page><PageHeader eyebrow="Laboratorio" title="Estadísticas" /><Alert title="No disponible">{error}</Alert></Page>;
  if (!stats)
    return (
      <Page>
        <PageHeader eyebrow="Laboratorio" title="Estadísticas" />
        <div className="grid gap-4 sm:grid-cols-3">
          {Array.from({ length: 3 }).map((_, i) => <Skeleton key={i} className="h-28" />)}
        </div>
      </Page>
    );

  const maxCmd = Math.max(1, ...stats.por_comando.map((c) => c.total));

  return (
    <Page>
      <PageHeader eyebrow="Laboratorio" title="Estadísticas del lab" />

      <div className="grid gap-4 sm:grid-cols-3">
        <Big label="Muestras" value={stats.samples.toLocaleString("es-MX")} />
        <Big label="Reportes en caché" value={stats.reports.toLocaleString("es-MX")} />
        <Big label="Datos analizados" value={humanSize(stats.bytes_total)} />
      </div>

      <div className="mt-6 grid gap-5 lg:grid-cols-2">
        <div className="card p-5 md:p-6">
          <h2 className="mb-4 flex items-center gap-2 font-display text-base font-bold text-white">
            <Chart width={18} height={18} className="text-guinda-300" /> Reportes por comando
          </h2>
          {stats.por_comando.length === 0 ? (
            <p className="text-sm text-slate-500">Aún no hay reportes cacheados.</p>
          ) : (
            <ul className="space-y-3">
              {stats.por_comando.map((c) => (
                <li key={c.kind}>
                  <div className="mb-1 flex items-center justify-between text-sm">
                    <span className="font-mono text-slate-300">{c.kind}</span>
                    <span className="text-slate-500">{c.total}</span>
                  </div>
                  <div className="h-2 overflow-hidden rounded-full bg-ink-700">
                    <motion.div
                      className="h-full rounded-full bg-gradient-to-r from-guinda-500 to-oro-400"
                      initial={{ width: 0 }}
                      animate={{ width: `${(c.total / maxCmd) * 100}%` }}
                      transition={{ duration: 0.7, ease: "easeOut" }}
                    />
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>

        <div className="card p-5 md:p-6">
          <h2 className="mb-4 font-display text-base font-bold text-white">Muestras recientes</h2>
          {stats.recientes.length === 0 ? (
            <EmptyState icon={<Chart width={26} height={26} />} title="Sin actividad" />
          ) : (
            <ul className="divide-y divide-line">
              {stats.recientes.map((s) => (
                <li key={s.sha256} className="flex items-center justify-between gap-3 py-3">
                  <div className="min-w-0">
                    <p className="truncate text-sm font-medium text-slate-200">{s.filename}</p>
                    <p className="font-mono text-xs text-slate-500">{shortSha(s.sha256, 18)}</p>
                  </div>
                  <div className="shrink-0 text-right">
                    <p className="text-sm text-slate-300">{humanSize(s.size)}</p>
                    <p className="text-xs text-slate-600">{fmtDate(s.uploaded_at)}</p>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </Page>
  );
}

function Big({ label, value }: { label: string; value: string }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      className="card relative overflow-hidden p-5"
    >
      <div className="absolute -right-6 -top-6 h-20 w-20 rounded-full bg-guinda-700/20 blur-2xl" />
      <p className="label">{label}</p>
      <p className="mt-2 font-display text-3xl font-extrabold text-white">{value}</p>
    </motion.div>
  );
}
