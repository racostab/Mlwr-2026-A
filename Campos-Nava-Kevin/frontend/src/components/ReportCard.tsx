import { motion } from "framer-motion";
import { useState } from "react";
import type { SampleReport } from "../api/types";
import { entropyTone, humanSize, shortSha } from "../lib/format";
import ResultView from "./ResultView";
import { CopyButton, Meter } from "./ui";

export default function ReportCard({
  report,
  index,
  total,
}: {
  report: SampleReport;
  index: number;
  total: number;
}) {
  const [active, setActive] = useState(0);
  const fileType = typeof report.mapa.file === "string" ? report.mapa.file : null;
  const entropyRaw = report.mapa.entropy;
  const entropy = typeof entropyRaw === "string" ? parseFloat(entropyRaw) : NaN;
  const hasEntropy = !Number.isNaN(entropy);

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35 }}
      className="card overflow-hidden"
    >
      <div className="border-b border-line p-5 md:p-6">
        <p className="eyebrow">
          Muestra {index + 1} de {total}
        </p>
        <h3 className="mt-1 break-all font-display text-lg font-bold text-white">
          {report.filename}
        </h3>
        <div className="mt-3 inline-flex max-w-full items-center gap-2 rounded-full border border-line bg-ink-950/60 py-1.5 pl-3.5 pr-1.5">
          <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500">SHA-256</span>
          <span className="truncate font-mono text-xs text-slate-300" title={report.sha256}>
            {shortSha(report.sha256, 28)}
          </span>
          <CopyButton value={report.sha256} label="Copiar SHA-256" />
        </div>

        <div className="mt-5 grid gap-3 sm:grid-cols-3">
          {fileType && (
            <Stat label="Tipo de archivo">
              <span className="font-mono text-[13px] leading-snug text-slate-200">{fileType}</span>
            </Stat>
          )}
          {hasEntropy && (
            <Stat label="Entropía">
              <span className="text-2xl font-bold text-white">
                {entropy.toFixed(2)}
                <span className="ml-1 text-xs font-medium text-slate-500">bits/byte</span>
              </span>
              <Meter value={entropy} />
              <span
                className={`text-xs ${
                  entropyTone(entropy) === "danger"
                    ? "text-danger"
                    : entropyTone(entropy) === "warn"
                      ? "text-warn"
                      : "text-ok"
                }`}
              >
                {entropyTone(entropy) === "danger"
                  ? "Alta — posible empaque/cifrado"
                  : entropyTone(entropy) === "warn"
                    ? "Media"
                    : "Baja"}
              </span>
            </Stat>
          )}
          <Stat label="Tamaño">
            <span className="text-2xl font-bold text-white">{humanSize(report.size)}</span>
            <span className="text-xs text-slate-500">{report.size.toLocaleString("es-MX")} bytes</span>
          </Stat>
        </div>
      </div>

      {/* Pestañas */}
      <div className="flex gap-1 overflow-x-auto border-b border-line px-3 pt-3">
        {report.resultados.map((r, i) => (
          <button
            key={i}
            onClick={() => setActive(i)}
            className={`relative whitespace-nowrap rounded-t-lg px-3.5 py-2.5 text-sm font-semibold transition ${
              active === i ? "text-white" : "text-slate-500 hover:text-slate-300"
            }`}
          >
            {r.etiqueta}
            {active === i && (
              <motion.span
                layoutId={`tab-${report.sha256}-${index}`}
                className="absolute inset-x-2 -bottom-px h-0.5 rounded-full bg-guinda-400"
              />
            )}
          </button>
        ))}
      </div>

      <div className="p-5 md:p-6">
        <motion.div
          key={active}
          initial={{ opacity: 0, y: 6 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.2 }}
        >
          {report.resultados[active] && <ResultView r={report.resultados[active]} />}
        </motion.div>
      </div>
    </motion.div>
  );
}

function Stat({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="flex flex-col gap-1.5 rounded-xl border border-line bg-ink-950/40 p-3.5">
      <span className="label">{label}</span>
      {children}
    </div>
  );
}
