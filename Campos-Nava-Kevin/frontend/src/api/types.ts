// Formas de datos que expone el motor (FastAPI :8001) y el servicio dinámico (:8002).

export interface Tool {
  id: string;
  etiqueta: string;
  cacheable: boolean;
  por_defecto: boolean;
}

export interface SampleMeta {
  sha256: string;
  filename: string;
  size: number;
}

export interface SampleRow extends SampleMeta {
  uploaded_at: string;
}

// El resultado de un analizador puede ser texto, lista, dict clave/valor o {matches}.
export type ToolResult =
  | string
  | string[]
  | { matches: string[]; error?: string }
  | Record<string, string>;

export type ResultKind = "matches" | "kv" | "lines" | "strings" | "text";

export interface RunResult {
  id: string; // id del analizador (o "custom")
  etiqueta: string;
  kind: ResultKind;
  result: ToolResult;
}

export interface SampleReport {
  sha256: string;
  filename: string;
  size: number;
  resultados: RunResult[];
  mapa: Record<string, ToolResult>;
  error?: string;
}

export interface ExperimentResult {
  numero: number;
  reports: SampleReport[];
  errors: { filename: string; error: string }[];
}

export interface Stats {
  samples: number;
  reports: number;
  bytes_total: number;
  por_comando: { kind: string; total: number }[];
  recientes: SampleRow[];
}

export interface YaraRuleFile {
  archivo: string;
  reglas: { nombre: string; descripcion: string }[];
  contenido: string;
}

export interface ComponentStatus {
  engine: string;
  db: string;
  sandbox: string;
  ok: boolean;
}

export interface GuidedCommand {
  comando: string;
  descripcion?: string;
  [k: string]: unknown;
}

// ---- Análisis dinámico ----
export interface DynamicState {
  vbox_disponible: boolean;
  vm: string;
  vm_existe: boolean;
  vm_corriendo: boolean;
  snapshot_limpio: boolean;
  en_cola: number;
}

export interface MitreTechnique {
  id: string;
  nombre: string;
  tactica: string;
  tactica_es: string;
  evidencia: string[];
}

export interface MitreMap {
  tecnicas: MitreTechnique[];
  n_tecnicas: number;
  grafo: {
    nodos: { id: string; tipo: string; label: string }[];
    aristas: { de: string; a: string }[];
  };
}

// Resultado del post-análisis del volcado: por cada volcado, lo que devolvieron
// las herramientas estáticas (yara → {matches}, strings → string[]).
export interface VolcadoAnalisis {
  sha256?: string;
  yara?: { matches: string[]; error?: string };
  strings?: string; // texto completo (strings -n N), una cadena por línea
  error?: string;
}
// `post_analisis` = { <archivo>: VolcadoAnalisis } (+ posible "_aviso": string).
export type PostAnalisis = Record<string, VolcadoAnalisis | string>;

export type DynamicJobState =
  | "en_cola"
  | "ejecutando"
  | "analizando_volcado"
  | "listo"
  | "error";

export interface DynamicJob {
  id: string;
  filename: string;
  segundos: number;
  estado: DynamicJobState;
  mensaje: string;
  creado: string;
  destino: string | null;
  archivos: string[];
  error: string | null;
  post_analisis?: PostAnalisis;
  mitre?: MitreMap;
}
