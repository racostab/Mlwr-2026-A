export function humanSize(bytes: number): string {
  if (!bytes) return "0 B";
  const units = ["B", "KB", "MB", "GB", "TB"];
  const i = Math.floor(Math.log(bytes) / Math.log(1024));
  const v = bytes / Math.pow(1024, i);
  return `${v.toFixed(v >= 10 || i === 0 ? 0 : 1)} ${units[i]}`;
}

export function shortSha(sha: string, n = 12): string {
  return sha.length > n ? `${sha.slice(0, n)}…${sha.slice(-4)}` : sha;
}

export function fmtDate(iso: string): string {
  try {
    return new Date(iso).toLocaleString("es-MX", {
      day: "2-digit",
      month: "short",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return iso;
  }
}

export async function copy(text: string): Promise<void> {
  try {
    await navigator.clipboard.writeText(text);
  } catch {
    /* clipboard no disponible (http sin permisos) */
  }
}

// La entropía Shannon va de 0 a 8 bits/byte; >7.2 suele indicar empaque/cifrado.
export function entropyTone(e: number): "ok" | "warn" | "danger" {
  if (e >= 7.2) return "danger";
  if (e >= 6) return "warn";
  return "ok";
}
