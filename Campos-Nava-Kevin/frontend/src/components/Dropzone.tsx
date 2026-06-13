import { useRef, useState } from "react";
import { humanSize } from "../lib/format";
import { FileBinary, Upload, X } from "./icons";

export default function Dropzone({
  files,
  onChange,
}: {
  files: File[];
  onChange: (files: File[]) => void;
}) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [drag, setDrag] = useState(false);

  const add = (list: FileList | null) => {
    if (!list) return;
    const incoming = Array.from(list);
    const merged = [...files];
    for (const f of incoming) {
      if (!merged.some((m) => m.name === f.name && m.size === f.size)) merged.push(f);
    }
    onChange(merged);
  };

  return (
    <div>
      <label
        onDragOver={(e) => {
          e.preventDefault();
          setDrag(true);
        }}
        onDragLeave={() => setDrag(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDrag(false);
          add(e.dataTransfer.files);
        }}
        className={`flex cursor-pointer flex-col items-center gap-2 rounded-xl border-2 border-dashed px-6 py-9 text-center transition ${
          drag
            ? "border-guinda-400 bg-guinda-700/10"
            : files.length
              ? "border-ok/50 bg-ok/5"
              : "border-line-strong bg-ink-950/40 hover:border-guinda-500"
        }`}
      >
        <span
          className={`grid h-12 w-12 place-items-center rounded-full ${
            files.length ? "bg-ok/15 text-ok" : "bg-guinda-700/20 text-guinda-300"
          }`}
        >
          <Upload width={22} height={22} />
        </span>
        <span className="font-semibold text-white">Arrastra las muestras aquí</span>
        <span className="text-sm text-slate-400">
          o <span className="text-guinda-300 underline underline-offset-2">elige desde tu equipo</span>{" "}
          (una o varias)
        </span>
        <input
          ref={inputRef}
          type="file"
          multiple
          className="hidden"
          onChange={(e) => add(e.target.files)}
        />
      </label>

      {files.length > 0 && (
        <ul className="mt-3 space-y-2">
          {files.map((f, i) => (
            <li
              key={f.name + f.size}
              className="flex items-center gap-3 rounded-lg border border-line bg-ink-900/60 px-3 py-2"
            >
              <FileBinary width={18} height={18} className="shrink-0 text-guinda-300" />
              <span className="min-w-0 flex-1 truncate text-sm text-slate-200">{f.name}</span>
              <span className="shrink-0 text-xs text-slate-500">{humanSize(f.size)}</span>
              <button
                type="button"
                onClick={() => onChange(files.filter((_, idx) => idx !== i))}
                className="grid h-7 w-7 shrink-0 place-items-center rounded-md text-slate-500 hover:bg-danger/10 hover:text-danger"
                aria-label={`Quitar ${f.name}`}
              >
                <X width={15} height={15} />
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
