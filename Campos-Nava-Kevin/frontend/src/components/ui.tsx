import { motion } from "framer-motion";
import { useState, type ReactNode } from "react";
import { copy } from "../lib/format";
import { Check, Copy } from "./icons";

// Transición de página estándar (la usa cada vista).
export function Page({ children }: { children: ReactNode }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 14 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -8 }}
      transition={{ duration: 0.35, ease: [0.22, 1, 0.36, 1] }}
    >
      {children}
    </motion.div>
  );
}

export function PageHeader({
  eyebrow,
  title,
  lead,
  right,
}: {
  eyebrow: string;
  title: string;
  lead?: ReactNode;
  right?: ReactNode;
}) {
  return (
    <header className="mb-8 flex flex-wrap items-end justify-between gap-4">
      <div className="max-w-2xl">
        <p className="eyebrow">{eyebrow}</p>
        <h1 className="mt-1.5 font-display text-3xl font-bold tracking-tight text-white md:text-4xl">
          {title}
        </h1>
        {lead && <p className="mt-3 text-slate-400">{lead}</p>}
      </div>
      {right}
    </header>
  );
}

export function Spinner({ className = "" }: { className?: string }) {
  return (
    <span
      className={`inline-block animate-spin rounded-full border-2 border-ink-600 border-t-guinda-400 ${className}`}
    />
  );
}

export function Alert({
  tone = "danger",
  title,
  children,
}: {
  tone?: "danger" | "warn" | "ok";
  title?: string;
  children: ReactNode;
}) {
  const tones = {
    danger: "border-danger/40 bg-danger/10 text-rose-200",
    warn: "border-warn/40 bg-warn/10 text-amber-100",
    ok: "border-ok/40 bg-ok/10 text-emerald-100",
  };
  return (
    <div className={`mb-5 rounded-xl border px-4 py-3 text-sm ${tones[tone]}`} role="alert">
      {title && <strong className="block font-semibold text-white">{title}</strong>}
      <div className="text-sm opacity-90">{children}</div>
    </div>
  );
}

export function StatusDot({ ok }: { ok: boolean }) {
  return (
    <span className="relative inline-flex h-2.5 w-2.5">
      {ok && (
        <span className="absolute inline-flex h-full w-full animate-pulse-ring rounded-full bg-ok" />
      )}
      <span
        className={`relative inline-flex h-2.5 w-2.5 rounded-full ${ok ? "bg-ok" : "bg-danger"}`}
      />
    </span>
  );
}

export function CopyButton({ value, label }: { value: string; label?: string }) {
  const [done, setDone] = useState(false);
  return (
    <button
      type="button"
      onClick={async () => {
        await copy(value);
        setDone(true);
        setTimeout(() => setDone(false), 1400);
      }}
      aria-label={label || "Copiar"}
      className={`grid h-8 w-8 place-items-center rounded-md border transition ${
        done
          ? "border-ok bg-ok/10 text-ok"
          : "border-line bg-ink-800/60 text-slate-400 hover:text-white"
      }`}
    >
      {done ? <Check width={14} height={14} /> : <Copy width={14} height={14} />}
    </button>
  );
}

export function Skeleton({ className = "" }: { className?: string }) {
  return <div className={`skeleton rounded-lg ${className}`} />;
}

export function EmptyState({
  icon,
  title,
  text,
  action,
}: {
  icon: ReactNode;
  title: string;
  text?: string;
  action?: ReactNode;
}) {
  return (
    <div className="card flex flex-col items-center px-6 py-16 text-center">
      <div className="mb-4 grid h-16 w-16 place-items-center rounded-2xl bg-ink-800 text-slate-500">
        {icon}
      </div>
      <h3 className="text-lg font-semibold text-white">{title}</h3>
      {text && <p className="mt-1 max-w-md text-sm text-slate-400">{text}</p>}
      {action && <div className="mt-5">{action}</div>}
    </div>
  );
}

export function Meter({ value, max = 8 }: { value: number; max?: number }) {
  const pct = Math.min(100, (value / max) * 100);
  const tone = value >= 7.2 ? "bg-danger" : value >= 6 ? "bg-warn" : "bg-ok";
  return (
    <div className="mt-1 h-1.5 w-full overflow-hidden rounded-full bg-ink-700">
      <motion.div
        className={`h-full rounded-full ${tone}`}
        initial={{ width: 0 }}
        animate={{ width: `${pct}%` }}
        transition={{ duration: 0.8, ease: "easeOut" }}
      />
    </div>
  );
}
