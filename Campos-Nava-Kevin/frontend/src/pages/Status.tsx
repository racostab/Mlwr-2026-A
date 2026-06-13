import { motion } from "framer-motion";
import { useEffect, useState } from "react";
import { getStatus } from "../api/client";
import type { ComponentStatus } from "../api/types";
import { Activity, Cpu } from "../components/icons";
import { Alert, Page, PageHeader, Skeleton, StatusDot } from "../components/ui";

const COMPONENTS = [
  { key: "engine" as const, name: "Motor (FastAPI)", desc: "Orquesta el análisis y la persistencia." },
  { key: "db" as const, name: "PostgreSQL", desc: "Historial de muestras y caché de reportes." },
  { key: "sandbox" as const, name: "Sandbox", desc: "Contenedor aislado que ejecuta las herramientas." },
];

export default function Status() {
  const [status, setStatus] = useState<ComponentStatus | null>(null);
  const [error, setError] = useState<string | null>(null);

  const tick = () =>
    getStatus()
      .then((s) => {
        setStatus(s);
        setError(null);
      })
      .catch((e) => setError(String(e.message ?? e)));

  useEffect(() => {
    tick();
    const id = setInterval(tick, 8000);
    return () => clearInterval(id);
  }, []);

  return (
    <Page>
      <PageHeader eyebrow="Sistema" title="Estado del laboratorio" />

      {error && <Alert title="El motor no respondió">{error}</Alert>}

      {!status && !error ? (
        <div className="grid gap-4 sm:grid-cols-3">
          {Array.from({ length: 3 }).map((_, i) => <Skeleton key={i} className="h-32" />)}
        </div>
      ) : status ? (
        <>
          <div
            className={`card mb-6 flex items-center gap-4 p-5 ${
              status.ok ? "border-ok/30" : "border-danger/30"
            }`}
          >
            <div className={`grid h-12 w-12 place-items-center rounded-xl ${status.ok ? "bg-ok/15 text-ok" : "bg-danger/15 text-danger"}`}>
              <Activity width={22} height={22} />
            </div>
            <div>
              <p className="font-display text-lg font-bold text-white">
                {status.ok ? "Todos los sistemas operativos" : "Hay incidencias"}
              </p>
              <p className="text-sm text-slate-400">
                {status.ok
                  ? "Motor, base de datos y sandbox responden correctamente."
                  : "Revisa los componentes marcados abajo."}
              </p>
            </div>
          </div>

          <div className="grid gap-4 sm:grid-cols-3">
            {COMPONENTS.map((c, i) => {
              const val = status[c.key];
              const ok = val === "ok";
              return (
                <motion.div
                  key={c.key}
                  initial={{ opacity: 0, y: 12 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.06 }}
                  className="card p-5"
                >
                  <div className="mb-3 flex items-center justify-between">
                    <span className="grid h-10 w-10 place-items-center rounded-lg bg-ink-800 text-guinda-300">
                      <Cpu width={19} height={19} />
                    </span>
                    <StatusDot ok={ok} />
                  </div>
                  <p className="font-semibold text-white">{c.name}</p>
                  <p className="mt-1 text-xs text-slate-400">{c.desc}</p>
                  <p className={`mt-3 font-mono text-xs ${ok ? "text-ok" : "text-danger"}`}>
                    {ok ? "● operativo" : val}
                  </p>
                </motion.div>
              );
            })}
          </div>
        </>
      ) : null}
    </Page>
  );
}
