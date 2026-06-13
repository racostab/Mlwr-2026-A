import { AnimatePresence, motion } from "framer-motion";
import { useState, type ReactNode } from "react";
import { NavLink } from "react-router-dom";
import Sidebar from "./Sidebar";
import { Menu, Shield, X } from "./icons";

export default function Layout({ children }: { children: ReactNode }) {
  const [open, setOpen] = useState(false);

  return (
    <div className="min-h-screen lg:grid lg:grid-cols-[270px_1fr]">
      {/* Sidebar fijo (escritorio) */}
      <aside className="sticky top-0 hidden h-screen border-r border-line bg-ink-900/60 backdrop-blur-xl lg:block">
        <Sidebar />
      </aside>

      {/* Drawer móvil */}
      <AnimatePresence>
        {open && (
          <>
            <motion.div
              className="fixed inset-0 z-40 bg-black/60 lg:hidden"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setOpen(false)}
            />
            <motion.aside
              className="fixed inset-y-0 left-0 z-50 w-72 border-r border-line bg-ink-900 lg:hidden"
              initial={{ x: "-100%" }}
              animate={{ x: 0 }}
              exit={{ x: "-100%" }}
              transition={{ type: "spring", stiffness: 380, damping: 38 }}
            >
              <Sidebar onNavigate={() => setOpen(false)} />
            </motion.aside>
          </>
        )}
      </AnimatePresence>

      <div className="flex min-w-0 flex-col">
        {/* Barra superior móvil */}
        <header className="sticky top-0 z-30 flex h-14 items-center gap-3 border-b border-line bg-ink-950/80 px-4 backdrop-blur-xl lg:hidden">
          <button
            onClick={() => setOpen((v) => !v)}
            className="grid h-9 w-9 place-items-center rounded-lg border border-line bg-ink-800 text-white"
            aria-label="Menú"
          >
            {open ? <X width={18} height={18} /> : <Menu width={18} height={18} />}
          </button>
          <NavLink to="/" className="flex items-center gap-2">
            <span className="grid h-8 w-8 place-items-center rounded-lg bg-gradient-to-br from-guinda-500 to-guinda-800 text-white">
              <Shield width={18} height={18} />
            </span>
            <span className="font-display font-bold text-white">
              Malware<span className="text-guinda-300">Lab</span>
            </span>
          </NavLink>
        </header>

        <main className="mx-auto w-full max-w-6xl flex-1 px-5 py-8 md:px-10 md:py-12">
          {children}
        </main>

        <footer className="border-t border-line px-5 py-6 text-xs text-slate-600 md:px-10">
          <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-2">
            <span>
              Malware Lab · Análisis estático (sandbox aislado) + dinámico (VM Kali)
            </span>
            <span className="text-slate-700">ESCOM · Instituto Politécnico Nacional</span>
          </div>
        </footer>
      </div>
    </div>
  );
}
