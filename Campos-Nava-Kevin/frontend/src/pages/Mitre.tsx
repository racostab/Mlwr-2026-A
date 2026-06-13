import { motion } from "framer-motion";
import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { listDynamicJobs } from "../api/client";
import type { DynamicJob, MitreTechnique } from "../api/types";
import { Target, Terminal } from "../components/icons";
import { Alert, EmptyState, Page, PageHeader } from "../components/ui";

export default function Mitre() {
  const [jobs, setJobs] = useState<DynamicJob[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    listDynamicJobs()
      .then(setJobs)
      .catch(() => setError("Servicio dinámico no disponible (el mapa ATT&CK se genera al detonar)."));
  }, []);

  const job = useMemo(
    () => (jobs ?? []).find((j) => (j.mitre?.tecnicas?.length ?? 0) > 0),
    [jobs],
  );

  const porTactica = useMemo(() => {
    const m = new Map<string, MitreTechnique[]>();
    for (const t of job?.mitre?.tecnicas ?? []) {
      const list = m.get(t.tactica_es) ?? [];
      list.push(t);
      m.set(t.tactica_es, list);
    }
    return [...m.entries()];
  }, [job]);

  return (
    <Page>
      <PageHeader
        eyebrow="Laboratorio"
        title="MITRE ATT&CK"
        lead="El mapa de técnicas se construye a partir de cada detonación dinámica: syscalls observadas (strace) y coincidencias YARA del volcado de memoria se traducen a técnicas ATT&CK con su táctica."
        right={
          <Link to="/dynamic" className="btn-ghost">
            <Terminal width={16} height={16} /> Ir a detonar
          </Link>
        }
      />

      {error && <Alert tone="warn" title="Sin conexión dinámica">{error}</Alert>}

      {jobs && !job ? (
        <EmptyState
          icon={<Target width={28} height={28} />}
          title="Aún no hay técnicas mapeadas"
          text="Detona una muestra en el análisis dinámico; al terminar, aquí verás su grafo táctica → técnica."
          action={
            <Link to="/dynamic" className="btn-primary">
              <Terminal width={16} height={16} /> Análisis dinámico
            </Link>
          }
        />
      ) : job ? (
        <>
          <p className="mb-5 text-sm text-slate-400">
            Última detonación con técnicas:{" "}
            <span className="font-mono text-guinda-200">{job.filename}</span> ·{" "}
            <strong className="text-white">{job.mitre?.n_tecnicas}</strong> técnicas en{" "}
            {porTactica.length} tácticas.
          </p>
          <div className="space-y-5">
            {porTactica.map(([tactica, tecnicas], gi) => (
              <motion.div
                key={tactica}
                initial={{ opacity: 0, y: 14 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: gi * 0.07 }}
                className="card p-5"
              >
                <div className="mb-4 flex items-center gap-2">
                  <span className="grid h-8 w-8 place-items-center rounded-lg bg-guinda-700/25 text-guinda-200">
                    <Target width={16} height={16} />
                  </span>
                  <h2 className="font-display text-base font-bold text-white">{tactica}</h2>
                  <span className="chip ml-auto">{tecnicas.length}</span>
                </div>
                <div className="grid gap-3 md:grid-cols-2">
                  {tecnicas.map((t) => (
                    <div key={t.id} className="rounded-xl border border-line bg-ink-950/40 p-4">
                      <div className="flex items-center gap-2">
                        <span className="rounded-md bg-guinda-700/30 px-2 py-0.5 font-mono text-[11px] font-bold text-guinda-200">
                          {t.id}
                        </span>
                        <span className="text-sm font-semibold text-white">{t.nombre}</span>
                      </div>
                      {t.evidencia.length > 0 && (
                        <ul className="mt-2 space-y-1">
                          {t.evidencia.slice(0, 4).map((e, i) => (
                            <li key={i} className="truncate font-mono text-[11px] text-slate-500" title={e}>
                              › {e}
                            </li>
                          ))}
                        </ul>
                      )}
                    </div>
                  ))}
                </div>
              </motion.div>
            ))}
          </div>
        </>
      ) : (
        <div className="space-y-2">
          <div className="skeleton h-40 rounded-2xl" />
        </div>
      )}
    </Page>
  );
}
