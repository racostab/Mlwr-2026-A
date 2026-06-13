import axios from "axios";
import type {
  ComponentStatus,
  DynamicJob,
  DynamicState,
  GuidedCommand,
  ResultKind,
  SampleMeta,
  SampleRow,
  Stats,
  Tool,
  ToolResult,
  YaraRuleFile,
} from "./types";

// El motor estático y el servicio dinámico se alcanzan por rutas relativas:
// en dev las resuelve el proxy de Vite, en prod nginx (ver nginx.conf). Se pueden
// sobreescribir con VITE_ENGINE_URL / VITE_DYNAMIC_URL si se sirve aparte.
const ENGINE = (import.meta.env.VITE_ENGINE_URL as string) || "/api";
const DYNAMIC = (import.meta.env.VITE_DYNAMIC_URL as string) || "/dynapi";

export const engine = axios.create({ baseURL: ENGINE });
export const dynamic = axios.create({ baseURL: DYNAMIC });

// ---------------- Motor estático ----------------

export async function getTools(): Promise<Tool[]> {
  const { data } = await engine.get<Tool[]>("/tools");
  return data;
}

export async function getCommands(): Promise<GuidedCommand[]> {
  const { data } = await engine.get<{ comandos: GuidedCommand[] }>("/commands");
  return data.comandos ?? [];
}

export async function getStats(): Promise<Stats> {
  const { data } = await engine.get<Stats>("/stats");
  return data;
}

export async function getStatus(): Promise<ComponentStatus> {
  const { data } = await engine.get<ComponentStatus>("/status");
  return data;
}

export async function getYaraRules(): Promise<YaraRuleFile[]> {
  const { data } = await engine.get<{ archivos: YaraRuleFile[] }>("/yara/rules");
  return data.archivos ?? [];
}

export async function getSamples(): Promise<SampleRow[]> {
  const { data } = await engine.get<SampleRow[]>("/samples");
  return data;
}

export async function uploadSample(file: File): Promise<SampleMeta> {
  const fd = new FormData();
  fd.append("file", file);
  const { data } = await engine.post<SampleMeta>("/samples", fd);
  return data;
}

export async function runTool(
  sha256: string,
  tool: string,
  opts: { min_len?: number; length?: number; cmd?: string } = {},
): Promise<ToolResult> {
  const { data } = await engine.get<{ tool: string; result: ToolResult }>(
    `/samples/${sha256}/run/${tool}`,
    { params: opts },
  );
  return data.result;
}

// Clasifica el resultado igual que el backend (web/servicios.py::_tipo).
export function classify(tool: string, result: ToolResult): ResultKind {
  if (tool === "strings") return "strings";
  if (result && typeof result === "object" && !Array.isArray(result)) {
    return "matches" in (result as object) ? "matches" : "kv";
  }
  if (Array.isArray(result)) return "lines";
  return "text";
}

// ---------------- Servicio dinámico (host) ----------------

export async function getDynamicState(): Promise<DynamicState> {
  const { data } = await dynamic.get<DynamicState>("/estado");
  return data;
}

export async function listDynamicJobs(): Promise<DynamicJob[]> {
  const { data } = await dynamic.get<DynamicJob[]>("/analisis");
  return data;
}

export async function createDynamicJob(file: File, segundos: number): Promise<DynamicJob> {
  const fd = new FormData();
  fd.append("file", file);
  fd.append("segundos", String(segundos));
  const { data } = await dynamic.post<DynamicJob>("/analisis", fd);
  return data;
}
