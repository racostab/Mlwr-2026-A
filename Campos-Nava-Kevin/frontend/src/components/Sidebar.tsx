import { motion } from "framer-motion";
import { NavLink } from "react-router-dom";
import { getStatus } from "../api/client";
import { useEffect, useState } from "react";
import type { ComponentStatus } from "../api/types";
import { Chart, Clock, Search, Shield, Target, Terminal } from "./icons";
import { StatusDot } from "./ui";

const groups = [
  {
    label: "Análisis",
    items: [
      { to: "/", icon: Search, text: "Analizar", end: true },
      { to: "/history", icon: Clock, text: "Historial" },
    ],
  },
  {
    label: "Laboratorio",
    items: [
      { to: "/dynamic", icon: Terminal, text: "Análisis dinámico" },
      { to: "/mitre", icon: Target, text: "MITRE ATT&CK" },
      { to: "/rules", icon: Shield, text: "Reglas YARA" },
      { to: "/stats", icon: Chart, text: "Estadísticas" },
    ],
  },
];

export default function Sidebar({ onNavigate }: { onNavigate?: () => void }) {
  const [status, setStatus] = useState<ComponentStatus | null>(null);
  const [down, setDown] = useState(false);

  useEffect(() => {
    let alive = true;
    const tick = () =>
      getStatus()
        .then((s) => alive && (setStatus(s), setDown(false)))
        .catch(() => alive && setDown(true));
    tick();
    const id = setInterval(tick, 15000);
    return () => {
      alive = false;
      clearInterval(id);
    };
  }, []);

  const ok = !down && !!status?.ok;

  return (
    <div className="flex h-full flex-col">
      <div className="border-b border-line px-5 py-5">
        <NavLink to="/" onClick={onNavigate} className="flex items-center gap-3">
          <motion.span
            whileHover={{ rotate: -6, scale: 1.05 }}
            className="grid h-10 w-10 place-items-center rounded-xl bg-gradient-to-br from-guinda-500 to-guinda-800 text-white shadow-glow"
          >
            <Shield width={22} height={22} />
          </motion.span>
          <span className="leading-tight">
            <span className="block font-display text-lg font-bold tracking-tight text-white">
              Malware<span className="text-guinda-300">Lab</span>
            </span>
            <span className="block text-[11px] font-medium uppercase tracking-[0.16em] text-slate-500">
              ESCOM · IPN
            </span>
          </span>
        </NavLink>
      </div>

      <nav className="flex-1 space-y-7 overflow-y-auto px-3 py-6">
        {groups.map((g) => (
          <div key={g.label}>
            <p className="px-3 pb-2 text-[10px] font-bold uppercase tracking-[0.14em] text-slate-600">
              {g.label}
            </p>
            <ul className="space-y-1">
              {g.items.map((it) => {
                const Icon = it.icon;
                return (
                  <li key={it.to}>
                    <NavLink
                      to={it.to}
                      end={it.end}
                      onClick={onNavigate}
                      className={({ isActive }) =>
                        `group relative flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition ${
                          isActive
                            ? "text-white"
                            : "text-slate-400 hover:bg-ink-800/70 hover:text-white"
                        }`
                      }
                    >
                      {({ isActive }) => (
                        <>
                          {isActive && (
                            <motion.span
                              layoutId="nav-active"
                              className="absolute inset-0 rounded-lg border border-guinda-500/40 bg-guinda-700/25"
                              transition={{ type: "spring", stiffness: 400, damping: 32 }}
                            />
                          )}
                          <Icon
                            width={18}
                            height={18}
                            className={`relative z-10 ${isActive ? "text-guinda-300" : ""}`}
                          />
                          <span className="relative z-10">{it.text}</span>
                        </>
                      )}
                    </NavLink>
                  </li>
                );
              })}
            </ul>
          </div>
        ))}
      </nav>

      <div className="border-t border-line px-5 py-4">
        <div className="flex items-center gap-2.5 rounded-lg border border-line bg-ink-900/60 px-3 py-2.5">
          <StatusDot ok={ok} />
          <div className="leading-tight">
            <p className="text-xs font-semibold text-white">
              {ok ? "Lab operativo" : "Lab con incidencias"}
            </p>
            <p className="text-[11px] text-slate-500">
              {down ? "motor sin respuesta" : "motor · db · sandbox"}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
