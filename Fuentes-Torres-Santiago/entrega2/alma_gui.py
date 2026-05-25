#!/usr/bin/env python3
# ============================================================
#  alma_gui.py  —  Cliente GUI del Laboratorio  [REDISEÑO]
#  Interfaz gráfica para el análisis estático de malware
#  Usa tkinter — incluido en Python base
#
#  Uso:
#    python alma_gui.py
#
#  Requiere:
#    alma_srv.py corriendo en localhost:9999
# ============================================================

import sys
import os
import socket
import json
import threading
import time
import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext, messagebox

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config

# ═══════════════════════════════════════════════════════════════
#  PALETA Y CONSTANTES DE DISEÑO
# ═══════════════════════════════════════════════════════════════

C = {
    # Fondos
    "bg_base":    "#0a0c0f",   # negro azulado profundo
    "bg_panel":   "#0f1318",   # panel ligeramente más claro
    "bg_widget":  "#161b22",   # widgets / entradas
    "bg_hover":   "#1c2330",   # hover
    "bg_header":  "#0d1117",   # header top

    # Texto
    "fg_primary":  "#e6edf3",  # texto principal
    "fg_secondary":"#8b949e",  # texto secundario / labels
    "fg_muted":    "#484f58",  # texto muy apagado

    # Acento principal — verde terminal
    "accent":      "#3fb950",  # verde activo
    "accent_dim":  "#238636",  # verde oscuro / bordes activos
    "accent_glow": "#56d364",  # verde brillante

    # Acento secundario — azul eléctrico
    "blue":        "#58a6ff",  # azul info
    "blue_dim":    "#1f6feb",  # azul oscuro

    # Estados
    "warn":        "#d29922",  # amarillo advertencia
    "warn_dim":    "#9e6a03",
    "danger":      "#f85149",  # rojo error
    "danger_dim":  "#da3633",
    "ok":          "#3fb950",  # verde ok

    # Bordes
    "border":      "#21262d",  # borde sutil
    "border_act":  "#30363d",  # borde activo

    # Output
    "bg_output":   "#060809",  # fondo área de resultados
    "fg_output":   "#b3c3d4",  # texto output
}

FONT_MONO  = ("Courier New", 9)
FONT_MONO_B= ("Courier New", 9, "bold")
FONT_MONO_L= ("Courier New", 10, "bold")
FONT_MONO_H= ("Courier New", 11, "bold")
FONT_SMALL = ("Courier New", 8)


# ═══════════════════════════════════════════════════════════════
#  COMUNICACIÓN CON SERVIDOR
# ═══════════════════════════════════════════════════════════════

def enviar_comando(accion, parametros={}):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(config.TIMEOUT)
        s.connect((config.SRV_HOST, config.SRV_PORT))
        s.sendall(json.dumps(
            {"accion": accion, "parametros": parametros}
        ).encode("utf-8"))
        respuesta = b""
        while True:
            parte = s.recv(config.BUFFER)
            if not parte:
                break
            respuesta += parte
            if len(parte) < config.BUFFER:
                break
        s.close()
        return json.loads(respuesta.decode("utf-8"))
    except ConnectionRefusedError:
        return {"status": "error", "mensaje": "Servidor no disponible"}
    except socket.timeout:
        return {"status": "error", "mensaje": "Timeout — servidor no respondio"}
    except Exception as e:
        return {"status": "error", "mensaje": str(e)}


def formatear_respuesta(respuesta):
    if not respuesta:
        return "[ERROR] Sin respuesta del servidor."
    if respuesta.get("status") == "error":
        return f"[ERROR] {respuesta.get('mensaje', 'Error desconocido')}"
    if "mensaje" in respuesta:
        return f"[OK] {respuesta['mensaje']}"
    if "stdout" in respuesta:
        out = respuesta.get("stdout", "")
        err = respuesta.get("stderr", "")
        return f"{out}\n{err}".strip()
    if "resultado" in respuesta:
        r    = respuesta["resultado"]
        modo = respuesta.get("modo", "docker").upper()
        SEP  = "─" * 56
        SEP2 = "═" * 56
        lineas = []

        lineas.append(SEP2)
        lineas.append(f"  RESULTADO  ·  modo: {modo}")
        lineas.append(SEP2)

        if "tipo_file" in r:
            lineas.append("\n  ▸ FILE")
            lineas.append(f"    {r['tipo_file']}")

        if "tipo" in r:
            t = r["tipo"]
            lineas.append("\n  ▸ TIPO DE ARCHIVO")
            lineas.append(f"    {t['tipo']}  ·  {t['descripcion']}  ({t['extension']})")

        if "hashes" in r:
            h = r["hashes"]
            lineas.append("\n  ▸ HASHES")
            lineas.append(f"    MD5    {h['md5']}")
            lineas.append(f"    SHA1   {h['sha1']}")
            lineas.append(f"    SHA256 {h['sha256']}")

        if "entropia" in r:
            e      = r["entropia"]
            estado = "⚠  SOSPECHOSO" if e["sospechoso"] else "✓  NORMAL"
            lineas.append("\n  ▸ ENTROPÍA")
            lineas.append(f"    {e['entropia']} / 8.0  ·  {e['nivel']}  ·  {estado}")

        if "exiftool" in r:
            lineas.append("\n  ▸ EXIFTOOL")
            for linea in r["exiftool"].split("\n")[:15]:
                lineas.append(f"    {linea}")

        if "strings" in r:
            lineas.append(f"\n  ▸ STRINGS  (primeras 10)")
            for i, s in enumerate(r["strings"][:10]):
                lineas.append(f"    {i+1:>3}.  {s}")

        if "cadenas" in r:
            c = r["cadenas"]
            lineas.append(f"\n  ▸ CADENAS  ·  {c['total']} encontradas")
            for i, s in enumerate(c["muestra"][:10]):
                lineas.append(f"    {i+1:>3}.  {s}")

        if "ssdeep_nativo" in r:
            lineas.append("\n  ▸ SSDEEP NATIVO")
            lineas.append(f"    {r['ssdeep_nativo']}")

        if "ssdeep" in r:
            lineas.append("\n  ▸ FUZZY HASH")
            lineas.append(f"    {r['ssdeep']['hash']}")

        if "laboratorio" in r:
            lineas.append("\n  ▸ ANÁLISIS PYTHON")
            lineas.append(r["laboratorio"])

        lineas.append(f"\n{SEP2}\n")
        return "\n".join(lineas)

    return json.dumps(respuesta, indent=2, ensure_ascii=False)


# ═══════════════════════════════════════════════════════════════
#  WIDGETS PERSONALIZADOS
# ═══════════════════════════════════════════════════════════════

class PanelLabel(tk.Frame):
    """Encabezado de sección con línea decorativa y badge."""

    def __init__(self, parent, titulo, icono="◈", **kwargs):
        super().__init__(parent, bg=C["bg_panel"], **kwargs)

        # Línea superior decorativa
        tk.Frame(self, bg=C["border_act"], height=1).pack(fill="x")

        inner = tk.Frame(self, bg=C["bg_panel"], pady=6, padx=10)
        inner.pack(fill="x")

        # Icono + título
        tk.Label(
            inner,
            text=f"{icono}  {titulo}",
            font=FONT_MONO_B,
            bg=C["bg_panel"],
            fg=C["accent"],
        ).pack(side="left")


class EntradaEstilizada(tk.Entry):
    """Entry con estilo consistente y soporte de placeholder."""

    def __init__(self, parent, placeholder="", **kwargs):
        super().__init__(
            parent,
            font=FONT_MONO,
            bg=C["bg_widget"],
            fg=C["fg_primary"],
            insertbackground=C["accent"],
            selectbackground=C["accent_dim"],
            selectforeground=C["fg_primary"],
            relief="flat",
            bd=0,
            **kwargs
        )
        self._placeholder = placeholder
        self._placeholder_active = False

        if placeholder:
            self._poner_placeholder()
            self.bind("<FocusIn>",  self._quitar_placeholder)
            self.bind("<FocusOut>", self._revisar_placeholder)

    def _poner_placeholder(self):
        self.insert(0, self._placeholder)
        self.config(fg=C["fg_muted"])
        self._placeholder_active = True

    def _quitar_placeholder(self, _=None):
        if self._placeholder_active:
            self.delete(0, tk.END)
            self.config(fg=C["fg_primary"])
            self._placeholder_active = False

    def _revisar_placeholder(self, _=None):
        if not self.get():
            self._poner_placeholder()

    def valor(self):
        """Retorna el valor real (ignorando placeholder)."""
        if self._placeholder_active:
            return ""
        return self.get().strip()


class BotonAccion(tk.Label):
    """Botón custom con hover y estados visuales."""

    def __init__(self, parent, texto, comando,
                 variante="default", ancho=None, **kwargs):

        esquemas = {
            "default": {
                "bg":     C["bg_widget"],
                "fg":     C["fg_primary"],
                "hover":  C["bg_hover"],
                "border": C["border_act"],
            },
            "primary": {
                "bg":     C["accent_dim"],
                "fg":     C["accent_glow"],
                "hover":  C["accent"],
                "border": C["accent"],
            },
            "danger": {
                "bg":     C["bg_widget"],
                "fg":     C["danger"],
                "hover":  C["danger_dim"],
                "border": C["danger_dim"],
            },
            "info": {
                "bg":     C["bg_widget"],
                "fg":     C["blue"],
                "hover":  C["blue_dim"],
                "border": C["blue_dim"],
            },
        }

        self._esquema  = esquemas.get(variante, esquemas["default"])
        self._comando  = comando
        self._texto    = texto

        padx = 10
        if ancho:
            padx = 0

        super().__init__(
            parent,
            text=texto,
            font=FONT_MONO_B,
            bg=self._esquema["bg"],
            fg=self._esquema["fg"],
            cursor="hand2",
            relief="flat",
            padx=padx, pady=5,
            **kwargs
        )

        if ancho:
            self.config(width=ancho, anchor="center")

        # Borde con canvas (workaround para bordes en tk.Label)
        self.bind("<Enter>",        self._on_enter)
        self.bind("<Leave>",        self._on_leave)
        self.bind("<Button-1>",     self._on_click)
        self.bind("<ButtonRelease-1>", self._on_release)

    def _on_enter(self, _):
        self.config(bg=self._esquema["hover"],
                    fg=C["fg_primary"])

    def _on_leave(self, _):
        self.config(bg=self._esquema["bg"],
                    fg=self._esquema["fg"])

    def _on_click(self, _):
        self.config(bg=C["fg_muted"])

    def _on_release(self, _):
        self.config(bg=self._esquema["hover"])
        if self._comando:
            self._comando()


class IndicadorEstado(tk.Frame):
    """Indicador LED + texto de estado."""

    ESTADOS = {
        "verificando": ("#d29922", "VERIFICANDO..."),
        "conectado":   ("#3fb950", "SERVIDOR ACTIVO"),
        "error":       ("#f85149", "SIN CONEXIÓN"),
    }

    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg=C["bg_header"], **kwargs)
        self._estado_actual = "verificando"
        self._blink_id = None

        self.canvas_led = tk.Canvas(
            self, width=10, height=10,
            bg=C["bg_header"], highlightthickness=0
        )
        self.canvas_led.pack(side="left", padx=(0, 6))
        self._led = self.canvas_led.create_oval(
            1, 1, 9, 9, fill="#d29922", outline=""
        )

        self.lbl = tk.Label(
            self,
            text="VERIFICANDO...",
            font=FONT_SMALL,
            bg=C["bg_header"],
            fg="#d29922",
        )
        self.lbl.pack(side="left")

    def set_estado(self, estado):
        color, texto = self.ESTADOS.get(
            estado, ("#484f58", estado.upper())
        )
        self._estado_actual = estado

        # Detener blink previo
        if self._blink_id:
            self.after_cancel(self._blink_id)
            self._blink_id = None

        self.canvas_led.itemconfig(self._led, fill=color)
        self.lbl.config(text=texto, fg=color)

        # Blink suave si hay error
        if estado == "error":
            self._iniciar_blink(color)

    def _iniciar_blink(self, color, visible=True):
        self.canvas_led.itemconfig(
            self._led,
            fill=color if visible else C["bg_header"]
        )
        self._blink_id = self.after(
            700,
            lambda: self._iniciar_blink(color, not visible)
        )


class BarraProgreso(tk.Frame):
    """Barra de progreso minimalista con texto."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg=C["bg_base"], **kwargs)
        self._visible = False

        self._frm = tk.Frame(self, bg=C["bg_base"])
        self._frm.pack(fill="x", padx=10, pady=2)

        self.lbl = tk.Label(
            self._frm, text="",
            font=FONT_SMALL,
            bg=C["bg_base"],
            fg=C["fg_secondary"],
            anchor="w"
        )
        self.lbl.pack(fill="x")

        self._barra_bg = tk.Frame(
            self._frm, bg=C["border"], height=2
        )
        self._barra_bg.pack(fill="x")

        self._barra = tk.Frame(
            self._barra_bg, bg=C["accent"], height=2
        )
        self._barra.place(relx=0, rely=0, relwidth=0, relheight=1)

        self._anim_id = None
        self._pos = 0.0

    def iniciar(self, texto="Procesando..."):
        self.lbl.config(text=texto)
        self._visible = True
        self._animar()

    def _animar(self):
        if not self._visible:
            return
        self._pos = (self._pos + 0.02) % 1.2
        w = 0.3
        x = self._pos - w
        # efecto "wipe" de izquierda a derecha
        rel_x = max(0.0, x)
        rel_w = min(w, 1.0 - rel_x)
        if rel_w > 0:
            self._barra.place(relx=rel_x, rely=0,
                              relwidth=rel_w, relheight=1)
        self._anim_id = self.after(30, self._animar)

    def detener(self, texto="Listo"):
        self._visible = False
        if self._anim_id:
            self.after_cancel(self._anim_id)
        self._barra.place(relx=0, rely=0, relwidth=0, relheight=1)
        self.lbl.config(text=texto)


# ═══════════════════════════════════════════════════════════════
#  APLICACIÓN PRINCIPAL
# ═══════════════════════════════════════════════════════════════

class LabApp:

    def __init__(self, root):
        self.root = root
        self.root.title("ALMA  ·  Laboratorio de Análisis de Malware")
        self.root.geometry("1060x720")
        self.root.minsize(860, 580)
        self.root.resizable(True, True)
        self.root.configure(bg=C["bg_base"])

        self._construir_ui()
        self._verificar_servidor()

    # ───────────────────────────────────────────────────────────
    #  CONSTRUCCIÓN DE UI
    # ───────────────────────────────────────────────────────────

    def _construir_ui(self):

        # ── Barra superior (header) ────────────────────────────
        self._construir_header()

        # ── Cuerpo principal ───────────────────────────────────
        frm_cuerpo = tk.Frame(self.root, bg=C["bg_base"])
        frm_cuerpo.pack(fill="both", expand=True, padx=0, pady=0)

        # Sidebar izquierda (controles)
        self._sidebar = tk.Frame(
            frm_cuerpo,
            bg=C["bg_panel"],
            width=270
        )
        self._sidebar.pack(side="left", fill="y")
        self._sidebar.pack_propagate(False)

        # Separador vertical
        tk.Frame(
            frm_cuerpo, bg=C["border"], width=1
        ).pack(side="left", fill="y")

        # Área de resultados
        frm_resultado = tk.Frame(frm_cuerpo, bg=C["bg_base"])
        frm_resultado.pack(side="left", fill="both", expand=True)

        self._construir_sidebar(self._sidebar)
        self._construir_resultados(frm_resultado)

        # ── Barra de estado inferior ───────────────────────────
        self._construir_statusbar()

    # ── Header ────────────────────────────────────────────────

    def _construir_header(self):
        header = tk.Frame(self.root, bg=C["bg_header"], pady=0)
        header.pack(fill="x")

        # Línea de acento superior
        tk.Frame(self.root, bg=C["accent_dim"], height=2).pack(
            fill="x"
        )

        inner = tk.Frame(header, bg=C["bg_header"])
        inner.pack(fill="x", padx=14, pady=8)

        # Logo / título
        frm_titulo = tk.Frame(inner, bg=C["bg_header"])
        frm_titulo.pack(side="left")

        tk.Label(
            frm_titulo,
            text="◈ ALMA",
            font=("Courier New", 14, "bold"),
            bg=C["bg_header"],
            fg=C["accent"],
        ).pack(side="left", padx=(0, 8))

        tk.Label(
            frm_titulo,
            text="Malware Lab Analyzer",
            font=FONT_MONO,
            bg=C["bg_header"],
            fg=C["fg_secondary"],
        ).pack(side="left")

        # Badge versión
        tk.Label(
            frm_titulo,
            text=" v2.0 ",
            font=FONT_SMALL,
            bg=C["accent_dim"],
            fg=C["accent_glow"],
        ).pack(side="left", padx=8)

        # Indicador de estado del servidor
        self.indicador = IndicadorEstado(inner)
        self.indicador.pack(side="right")

        # Línea separadora inferior del header
        tk.Frame(self.root, bg=C["border"], height=1).pack(fill="x")

    # ── Sidebar ────────────────────────────────────────────────

    def _construir_sidebar(self, parent):

        # ── SECCIÓN: ANÁLISIS ──────────────────────────────────
        PanelLabel(parent, "ANÁLISIS", "⬡").pack(fill="x")

        frm_analisis = tk.Frame(parent, bg=C["bg_panel"], padx=10)
        frm_analisis.pack(fill="x", pady=(4, 0))

        # Label + entry archivo en fila
        tk.Label(
            frm_analisis,
            text="ARCHIVO  /  MUESTRA",
            font=FONT_SMALL,
            bg=C["bg_panel"],
            fg=C["fg_secondary"],
        ).pack(anchor="w", pady=(4, 2))

        frm_fila = tk.Frame(frm_analisis, bg=C["bg_panel"])
        frm_fila.pack(fill="x", pady=(0, 6))

        # Borde visual alrededor del entry
        frm_entrada_border = tk.Frame(
            frm_fila, bg=C["border_act"], padx=1, pady=1
        )
        frm_entrada_border.pack(side="left", fill="x",
                                expand=True, padx=(0, 4))

        self.entry_archivo = EntradaEstilizada(
            frm_entrada_border,
            placeholder="ruta/al/archivo..."
        )
        self.entry_archivo.pack(fill="x", padx=4, pady=2)

        BotonAccion(
            frm_fila, "  …  ",
            self._buscar_archivo,
            variante="info"
        ).pack(side="left")

        # Botones análisis
        frm_btns_an = tk.Frame(frm_analisis, bg=C["bg_panel"])
        frm_btns_an.pack(fill="x", pady=(0, 10))

        BotonAccion(
            frm_btns_an,
            "▶  Analizar archivo",
            self._analizar_archivo,
            variante="primary",
        ).pack(fill="x", pady=(0, 3))

        BotonAccion(
            frm_btns_an,
            "⊞  Analizar carpeta",
            self._analizar_carpeta,
            variante="default",
        ).pack(fill="x")

        # ── SECCIÓN: VIRTUALBOX ────────────────────────────────
        PanelLabel(parent, "VIRTUALBOX", "⬡").pack(fill="x", pady=(6,0))

        frm_vm = tk.Frame(parent, bg=C["bg_panel"], padx=10)
        frm_vm.pack(fill="x", pady=(4, 0))

        tk.Label(
            frm_vm,
            text="NOMBRE DE VM",
            font=FONT_SMALL,
            bg=C["bg_panel"],
            fg=C["fg_secondary"],
        ).pack(anchor="w", pady=(4, 2))

        frm_vm_b = tk.Frame(frm_vm, bg=C["border_act"], padx=1, pady=1)
        frm_vm_b.pack(fill="x", pady=(0, 6))

        self.entry_vm = EntradaEstilizada(frm_vm_b)
        self.entry_vm.insert(0, config.VM_NOMBRE)
        self.entry_vm.pack(fill="x", padx=4, pady=2)

        frm_vm_btns = tk.Frame(frm_vm, bg=C["bg_panel"])
        frm_vm_btns.pack(fill="x", pady=(0, 10))

        for texto, cmd in [("LIST","list"),("START","start"),
                           ("STOP","stop"),("STATUS","status")]:
            BotonAccion(
                frm_vm_btns, texto,
                lambda c=cmd: self._vm_cmd(c),
                variante="default", ancho=7
            ).pack(side="left", padx=(0, 3))

        # ── SECCIÓN: DOCKER ────────────────────────────────────
        PanelLabel(parent, "DOCKER", "⬡").pack(fill="x", pady=(6,0))

        frm_dock = tk.Frame(parent, bg=C["bg_panel"], padx=10)
        frm_dock.pack(fill="x", pady=(4, 0))

        tk.Label(
            frm_dock,
            text="NOMBRE DE CONTENEDOR",
            font=FONT_SMALL,
            bg=C["bg_panel"],
            fg=C["fg_secondary"],
        ).pack(anchor="w", pady=(4, 2))

        frm_dock_b = tk.Frame(frm_dock, bg=C["border_act"], padx=1, pady=1)
        frm_dock_b.pack(fill="x", pady=(0, 6))

        self.entry_docker = EntradaEstilizada(frm_dock_b)
        self.entry_docker.insert(0, config.DOCKER_CONTENEDOR)
        self.entry_docker.pack(fill="x", padx=4, pady=2)

        frm_dock_btns = tk.Frame(frm_dock, bg=C["bg_panel"])
        frm_dock_btns.pack(fill="x", pady=(0, 10))

        for texto, cmd in [("LIST","list"),("START","start"),
                           ("STOP","stop"),("LOGS","logs")]:
            BotonAccion(
                frm_dock_btns, texto,
                lambda c=cmd: self._docker_cmd(c),
                variante="default", ancho=7
            ).pack(side="left", padx=(0, 3))

        # ── SECCIÓN: SERVIDOR ──────────────────────────────────
        PanelLabel(parent, "SERVIDOR", "⬡").pack(fill="x", pady=(6,0))

        frm_srv = tk.Frame(parent, bg=C["bg_panel"], padx=10)
        frm_srv.pack(fill="x", pady=(4, 0))

        BotonAccion(
            frm_srv,
            "◎  Ping al servidor",
            self._ping,
            variante="info",
        ).pack(fill="x", pady=(4, 10))

        # ── Relleno inferior ───────────────────────────────────
        tk.Frame(parent, bg=C["bg_panel"]).pack(fill="both", expand=True)

        # Firma inferior del sidebar
        tk.Label(
            parent,
            text=f"  {config.SRV_HOST}:{config.SRV_PORT}  ·  Mlwr-2026-A",
            font=FONT_SMALL,
            bg=C["bg_panel"],
            fg=C["fg_muted"],
            anchor="w",
        ).pack(fill="x", padx=10, pady=6)

    # ── Panel de resultados ────────────────────────────────────

    def _construir_resultados(self, parent):

        # Header del panel resultados
        frm_res_top = tk.Frame(parent, bg=C["bg_base"])
        frm_res_top.pack(fill="x", padx=12, pady=(8, 4))

        tk.Label(
            frm_res_top,
            text="RESULTADOS",
            font=FONT_MONO_B,
            bg=C["bg_base"],
            fg=C["accent"],
        ).pack(side="left")

        # Tabs / breadcrumb visual (estático, solo estética)
        self.lbl_contexto = tk.Label(
            frm_res_top,
            text="",
            font=FONT_SMALL,
            bg=C["bg_base"],
            fg=C["fg_muted"],
        )
        self.lbl_contexto.pack(side="left", padx=10)

        # Botones del panel de resultados
        frm_res_btns = tk.Frame(frm_res_top, bg=C["bg_base"])
        frm_res_btns.pack(side="right")

        BotonAccion(
            frm_res_btns, "⊟  Limpiar",
            self._limpiar, variante="default"
        ).pack(side="left", padx=(0, 6))

        BotonAccion(
            frm_res_btns, "⬇  Guardar",
            self._guardar, variante="default"
        ).pack(side="left")

        # Línea separadora
        tk.Frame(parent, bg=C["border"], height=1).pack(
            fill="x", padx=12
        )

        # Área de texto
        frm_output = tk.Frame(parent, bg=C["bg_output"])
        frm_output.pack(fill="both", expand=True, padx=12, pady=(6, 4))

        # Borde izquierdo decorativo (línea de color)
        tk.Frame(
            frm_output, bg=C["accent_dim"], width=3
        ).pack(side="left", fill="y")

        self.txt_resultado = scrolledtext.ScrolledText(
            frm_output,
            font=("Courier New", 9),
            bg=C["bg_output"],
            fg=C["fg_output"],
            insertbackground=C["accent"],
            selectbackground=C["accent_dim"],
            relief="flat",
            wrap="word",
            bd=0,
            padx=12,
            pady=8,
        )
        self.txt_resultado.pack(fill="both", expand=True)

        # Configurar tags de color para el output
        self._configurar_tags_output()

    def _configurar_tags_output(self):
        t = self.txt_resultado
        t.tag_config("header",    foreground=C["accent"],
                     font=("Courier New", 9, "bold"))
        t.tag_config("seccion",   foreground=C["blue"],
                     font=("Courier New", 9, "bold"))
        t.tag_config("ok",        foreground=C["ok"])
        t.tag_config("warn",      foreground=C["warn"])
        t.tag_config("error",     foreground=C["danger"])
        t.tag_config("muted",     foreground=C["fg_muted"])
        t.tag_config("valor",     foreground=C["fg_primary"])
        t.tag_config("separador", foreground=C["border_act"])

    # ── Status bar ─────────────────────────────────────────────

    def _construir_statusbar(self):
        tk.Frame(self.root, bg=C["border"], height=1).pack(fill="x")

        bar = tk.Frame(self.root, bg=C["bg_panel"], pady=0)
        bar.pack(fill="x")

        inner = tk.Frame(bar, bg=C["bg_panel"])
        inner.pack(fill="x", padx=12, pady=4)

        self.lbl_status = tk.Label(
            inner,
            text="Sistema listo.",
            font=FONT_SMALL,
            bg=C["bg_panel"],
            fg=C["fg_secondary"],
            anchor="w",
        )
        self.lbl_status.pack(side="left", fill="x", expand=True)

        # Hora en la esquina derecha
        self.lbl_hora = tk.Label(
            inner,
            text="",
            font=FONT_SMALL,
            bg=C["bg_panel"],
            fg=C["fg_muted"],
        )
        self.lbl_hora.pack(side="right")
        self._actualizar_hora()

        # Barra de progreso encima del status bar
        self.barra = BarraProgreso(self.root)
        self.barra.pack(fill="x")
        # La reposicionamos antes del status (orden inverso por pack)
        self.barra.pack_forget()
        self.barra.pack(fill="x", before=bar)

    def _actualizar_hora(self):
        hora = time.strftime("%H:%M:%S")
        self.lbl_hora.config(text=hora)
        self.root.after(1000, self._actualizar_hora)

    # ───────────────────────────────────────────────────────────
    #  HELPERS DE UI
    # ───────────────────────────────────────────────────────────

    def _log(self, texto, limpiar=False, tag=None):
        """Escribe en el área de resultados con coloreo básico."""
        if limpiar:
            self.txt_resultado.delete("1.0", tk.END)

        # Coloreo automático por contenido
        lineas = texto.split("\n")
        for linea in lineas:
            l = linea.strip()
            if l.startswith("═") or l.startswith("─"):
                t = "separador"
            elif l.startswith("▸") or l.startswith("[") and "]" in l:
                t = "seccion"
            elif "ERROR" in l or "⚠" in l:
                t = "error" if "ERROR" in l else "warn"
            elif "[OK]" in l or "✓" in l:
                t = "ok"
            elif tag:
                t = tag
            else:
                t = None

            if t:
                self.txt_resultado.insert(tk.END, linea + "\n", t)
            else:
                self.txt_resultado.insert(tk.END, linea + "\n")

        self.txt_resultado.see(tk.END)

    def _status(self, texto, tipo="normal"):
        colores = {
            "normal":  C["fg_secondary"],
            "ok":      C["ok"],
            "warn":    C["warn"],
            "error":   C["danger"],
            "working": C["blue"],
        }
        self.lbl_status.config(
            text=f"›  {texto}",
            fg=colores.get(tipo, C["fg_secondary"])
        )
        self.root.update_idletasks()

    def _contexto(self, texto):
        self.lbl_contexto.config(text=texto)

    def _en_hilo(self, fn):
        threading.Thread(target=fn, daemon=True).start()

    # ───────────────────────────────────────────────────────────
    #  ACCIONES
    # ───────────────────────────────────────────────────────────

    def _verificar_servidor(self):
        def _check():
            self.indicador.set_estado("verificando")
            r = enviar_comando("ping")
            if r.get("status") == "ok":
                self.indicador.set_estado("conectado")
                self._status(
                    f"Servidor activo en "
                    f"{config.SRV_HOST}:{config.SRV_PORT}", "ok"
                )
            else:
                self.indicador.set_estado("error")
                self._status(
                    "Servidor no disponible — ejecuta alma_srv.py",
                    "error"
                )
        self._en_hilo(_check)

    def _buscar_archivo(self):
        ruta = filedialog.askopenfilename(
            title="Seleccionar muestra a analizar",
            initialdir=config.EXPERIMENTOS_DIR
        )
        if ruta:
            self.entry_archivo._quitar_placeholder()
            self.entry_archivo.delete(0, tk.END)
            self.entry_archivo.insert(0, ruta)
            self.entry_archivo.config(fg=C["fg_primary"])
            self.entry_archivo._placeholder_active = False
            self._contexto(os.path.basename(ruta))

    def _analizar_archivo(self):
        archivo = self.entry_archivo.valor()
        if not archivo:
            messagebox.showwarning(
                "Sin archivo",
                "Selecciona o escribe la ruta del archivo a analizar."
            )
            return

        def _run():
            nombre = os.path.basename(archivo)
            self._status(f"Analizando: {nombre}", "working")
            self._contexto(nombre)
            self.barra.iniciar(f"Analizando {nombre}...")
            self._log(
                f"[INICIO]  {nombre}\n"
                f"[RUTA]    {archivo}\n",
                limpiar=True
            )
            r = enviar_comando("analizar", {
                "archivo": archivo, "modo": "docker"
            })
            self._log(formatear_respuesta(r))
            self.barra.detener("Análisis completado.")
            self._status("Análisis completado.", "ok")

        self._en_hilo(_run)

    def _analizar_carpeta(self):
        carpeta = filedialog.askdirectory(
            title="Seleccionar carpeta a analizar",
            initialdir=config.EXPERIMENTOS_DIR
        )
        if not carpeta:
            return

        def _run():
            archivos = [
                f for f in os.listdir(carpeta)
                if os.path.isfile(os.path.join(carpeta, f))
            ]
            if not archivos:
                self._log(
                    "[ERROR] No hay archivos en la carpeta seleccionada.",
                    limpiar=True
                )
                return

            self._contexto(os.path.basename(carpeta) + "/")
            self._log(
                f"[CARPETA]   {carpeta}\n"
                f"[ARCHIVOS]  {len(archivos)} encontrados\n",
                limpiar=True
            )

            hashes_ssdeep = {}

            for i, archivo in enumerate(archivos):
                ruta = os.path.join(carpeta, archivo)
                prog = f"[{i+1}/{len(archivos)}] {archivo}"
                self._status(prog, "working")
                self.barra.iniciar(prog)
                self._log(f"\n── {i+1}/{len(archivos)}  {archivo}")
                self._log("─" * 50)

                r = enviar_comando("analizar", {
                    "archivo": ruta, "modo": "docker"
                })
                self._log(formatear_respuesta(r))

                if r.get("status") == "ok":
                    res = r.get("resultado", {})
                    if "ssdeep_nativo" in res:
                        hashes_ssdeep[archivo] = res["ssdeep_nativo"]
                    elif "ssdeep" in res:
                        hashes_ssdeep[archivo] = res["ssdeep"]["hash"]

            # Comparación ssdeep
            if len(hashes_ssdeep) >= 2:
                from modulos.ssdeep import calcular_ssdeep, comparar
                SEP = "═" * 56
                self._log(f"\n{SEP}")
                self._log("  COMPARACIÓN DE SIMILITUD — SSDEEP")
                self._log(SEP)

                lista = list(hashes_ssdeep.keys())
                for i in range(len(lista)):
                    for j in range(i + 1, len(lista)):
                        a1 = lista[i]
                        a2 = lista[j]
                        r1 = calcular_ssdeep(os.path.join(carpeta, a1))
                        r2 = calcular_ssdeep(os.path.join(carpeta, a2))
                        sim = comparar(r1, r2)

                        if sim >= 80:
                            alerta = "⚠  POSIBLE VARIANTE"
                        elif sim >= 50:
                            alerta = "~  PARCIALMENTE SIMILARES"
                        else:
                            alerta = "✓  DIFERENTES"

                        self._log(
                            f"\n  {a1}\n"
                            f"  vs  {a2}\n"
                            f"  Similitud: {sim}%  ·  {alerta}"
                        )
                self._log(f"\n{SEP}\n")

            self.barra.detener("Análisis de carpeta completado.")
            self._status("Análisis de carpeta completado.", "ok")

        self._en_hilo(_run)

    def _vm_cmd(self, cmd):
        vm = self.entry_vm.get().strip() or config.VM_NOMBRE

        def _run():
            self._status(f"VirtualBox · {cmd.upper()} · {vm}", "working")
            self.barra.iniciar(f"VM {cmd}...")
            r = enviar_comando("vm", {"cmd": cmd, "vm": vm})
            self._log(
                f"\n[VM]  {cmd.upper()}  ·  {vm}\n"
                + formatear_respuesta(r)
            )
            self.barra.detener()
            self._status(f"VM {cmd} completado.", "ok")

        self._en_hilo(_run)

    def _docker_cmd(self, cmd):
        nombre = self.entry_docker.get().strip() \
                 or config.DOCKER_CONTENEDOR

        def _run():
            self._status(f"Docker · {cmd.upper()} · {nombre}", "working")
            self.barra.iniciar(f"Docker {cmd}...")
            r = enviar_comando("docker", {"cmd": cmd, "nombre": nombre})
            self._log(
                f"\n[DOCKER]  {cmd.upper()}  ·  {nombre}\n"
                + formatear_respuesta(r)
            )
            self.barra.detener()
            self._status(f"Docker {cmd} completado.", "ok")

        self._en_hilo(_run)

    def _ping(self):
        def _run():
            self._status("Enviando ping al servidor...", "working")
            self.barra.iniciar("Verificando conexión...")
            r = enviar_comando("ping")
            self._log("\n[PING]  " + formatear_respuesta(r))
            self.barra.detener()
            self._verificar_servidor()

        self._en_hilo(_run)

    def _limpiar(self):
        self.txt_resultado.delete("1.0", tk.END)
        self._contexto("")
        self._status("Listo.")

    def _guardar(self):
        contenido = self.txt_resultado.get("1.0", tk.END).strip()
        if not contenido:
            messagebox.showwarning(
                "Sin contenido",
                "No hay resultados que guardar."
            )
            return

        ruta = filedialog.asksaveasfilename(
            title="Guardar resultado",
            initialdir=config.RESULTADOS_DIR,
            defaultextension=".txt",
            filetypes=[("Texto", "*.txt"), ("Todos", "*.*")]
        )
        if ruta:
            with open(ruta, "w", encoding="utf-8") as f:
                f.write(contenido)
            self._status(
                f"Guardado: {os.path.basename(ruta)}", "ok"
            )


# ═══════════════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    root = tk.Tk()
    app  = LabApp(root)
    root.mainloop()