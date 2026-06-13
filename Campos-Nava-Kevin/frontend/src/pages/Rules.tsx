import { AnimatePresence, motion } from "framer-motion";
import { useEffect, useState } from "react";
import { getYaraRules } from "../api/client";
import type { YaraRuleFile } from "../api/types";
import { Shield } from "../components/icons";
import { Alert, EmptyState, Page, PageHeader, Skeleton } from "../components/ui";

export default function Rules() {
  const [files, setFiles] = useState<YaraRuleFile[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [open, setOpen] = useState<string | null>(null);

  useEffect(() => {
    getYaraRules()
      .then(setFiles)
      .catch((e) => setError(String(e.message ?? e)));
  }, []);

  const totalRules = (files ?? []).reduce((a, f) => a + f.reglas.length, 0);

  return (
    <Page>
      <PageHeader
        eyebrow="Laboratorio"
        title="Reglas YARA"
        lead="Reglas cargadas en el sandbox (/rules/*.yar). Son la fuente de verdad: se aplican igual al binario en disco y al volcado de memoria del análisis dinámico."
        right={files ? <span className="chip text-guinda-200">{totalRules} reglas</span> : undefined}
      />

      {error && <Alert title="No se pudieron leer las reglas">{error}</Alert>}

      {files === null ? (
        <div className="space-y-2">
          {Array.from({ length: 5 }).map((_, i) => <Skeleton key={i} className="h-16" />)}
        </div>
      ) : files.length === 0 ? (
        <EmptyState icon={<Shield width={28} height={28} />} title="Sin reglas cargadas" />
      ) : (
        <div className="space-y-3">
          {files.map((f) => {
            const name = f.archivo.split("/").pop() ?? f.archivo;
            const isOpen = open === f.archivo;
            return (
              <div key={f.archivo} className="card overflow-hidden">
                <button
                  onClick={() => setOpen(isOpen ? null : f.archivo)}
                  className="flex w-full items-center justify-between gap-3 px-5 py-4 text-left hover:bg-ink-800/40"
                >
                  <div className="flex items-center gap-3">
                    <span className="grid h-9 w-9 place-items-center rounded-lg bg-ink-800 text-guinda-300">
                      <Shield width={18} height={18} />
                    </span>
                    <div>
                      <p className="font-mono text-sm font-semibold text-white">{name}</p>
                      <p className="text-xs text-slate-500">{f.reglas.length} reglas</p>
                    </div>
                  </div>
                  <motion.span animate={{ rotate: isOpen ? 90 : 0 }} className="text-slate-500">
                    ▸
                  </motion.span>
                </button>

                <AnimatePresence initial={false}>
                  {isOpen && (
                    <motion.div
                      initial={{ height: 0, opacity: 0 }}
                      animate={{ height: "auto", opacity: 1 }}
                      exit={{ height: 0, opacity: 0 }}
                      className="overflow-hidden border-t border-line"
                    >
                      <div className="p-5">
                        <div className="mb-4 flex flex-wrap gap-2">
                          {f.reglas.map((r) => (
                            <span
                              key={r.nombre}
                              title={r.descripcion}
                              className="rounded-full border border-line-strong bg-ink-800/70 px-3 py-1 font-mono text-xs text-slate-300"
                            >
                              {r.nombre}
                            </span>
                          ))}
                        </div>
                        <pre className="max-h-80 overflow-auto rounded-xl border border-line bg-ink-950/70 p-4 font-mono text-[12px] leading-relaxed text-slate-400">
                          {f.contenido}
                        </pre>
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            );
          })}
        </div>
      )}
    </Page>
  );
}
