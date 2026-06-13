import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getTools } from "../api/client";
import type { Tool } from "../api/types";
import { Bolt, Book, Search, Shield, Target, Terminal } from "../components/icons";
import { Page, PageHeader } from "../components/ui";

export default function Docs() {
  const [tools, setTools] = useState<Tool[]>([]);
  useEffect(() => {
    getTools().then(setTools).catch(() => setTools([]));
  }, []);

  return (
    <Page>
      <PageHeader
        eyebrow="Sistema"
        title="Documentación"
        lead="Cómo funciona el laboratorio de análisis de malware: dos familias de análisis, totalmente aisladas del host."
      />

      <div className="grid gap-5 md:grid-cols-2">
        <Card icon={<Search width={20} height={20} />} title="Análisis estático" to="/">
          Sube binarios ELF y arma <strong>experimentos</strong> (N muestras + N comandos). Todo
          corre por SSH dentro de un contenedor sandbox sin red ni acceso al host. Las muestras
          nunca se ejecutan: solo se inspeccionan.
        </Card>
        <Card icon={<Terminal width={20} height={20} />} title="Análisis dinámico" to="/dynamic">
          Detona la muestra dentro de una VM Kali aislada (red host-only, sin NAT, firewall del
          host). Antes de ejecutar se restaura un snapshot limpio y se verifica la jaula; si hay
          fuga, se aborta. Corre bajo <code className="font-mono text-guinda-200">strace</code> y se
          vuelca la memoria.
        </Card>
        <Card icon={<Shield width={20} height={20} />} title="Reglas YARA" to="/rules">
          Las reglas viven una sola vez en el sandbox y se aplican igual al binario en disco y al
          volcado de memoria del análisis dinámico (donde los packers se desempaquetan).
        </Card>
        <Card icon={<Target width={20} height={20} />} title="MITRE ATT&CK" to="/mitre">
          Cada detonación traduce syscalls (strace) y coincidencias YARA del volcado a técnicas
          ATT&CK, agrupadas por táctica.
        </Card>
      </div>

      <div className="card mt-6 p-5 md:p-6">
        <h2 className="mb-4 flex items-center gap-2 font-display text-base font-bold text-white">
          <Bolt width={18} height={18} className="text-guinda-300" /> Catálogo de comandos estáticos
        </h2>
        {tools.length === 0 ? (
          <p className="text-sm text-slate-500">Catálogo no disponible.</p>
        ) : (
          <div className="grid gap-2 sm:grid-cols-2">
            {tools.map((t) => (
              <div
                key={t.id}
                className="flex items-center justify-between gap-3 rounded-lg border border-line bg-ink-950/40 px-3.5 py-2.5"
              >
                <div>
                  <p className="text-sm font-medium text-slate-200">{t.etiqueta}</p>
                  <p className="font-mono text-xs text-slate-500">id: {t.id}</p>
                </div>
                {t.por_defecto && (
                  <span className="rounded-full bg-guinda-700/30 px-2 py-0.5 text-[10px] font-bold uppercase text-guinda-200">
                    por defecto
                  </span>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="card mt-5 flex items-center gap-4 p-5">
        <span className="grid h-10 w-10 place-items-center rounded-lg bg-ink-800 text-guinda-300">
          <Book width={19} height={19} />
        </span>
        <p className="text-sm text-slate-400">
          ¿Listo para empezar? Ve a{" "}
          <Link to="/" className="font-semibold text-guinda-300 underline underline-offset-2">
            Analizar
          </Link>{" "}
          y crea tu primer experimento.
        </p>
      </div>
    </Page>
  );
}

function Card({
  icon,
  title,
  to,
  children,
}: {
  icon: React.ReactNode;
  title: string;
  to: string;
  children: React.ReactNode;
}) {
  return (
    <Link to={to} className="card card-hover block p-5 md:p-6">
      <div className="mb-3 grid h-11 w-11 place-items-center rounded-xl bg-gradient-to-br from-guinda-600 to-guinda-800 text-white">
        {icon}
      </div>
      <h3 className="font-display text-lg font-bold text-white">{title}</h3>
      <p className="mt-2 text-sm leading-relaxed text-slate-400">{children}</p>
    </Link>
  );
}
