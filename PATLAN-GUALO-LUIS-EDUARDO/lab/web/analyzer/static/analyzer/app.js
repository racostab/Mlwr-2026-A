/* Malware Lab — SPA (Vue 3, sin paso de compilación).
 * El SPA habla directo con la API del engine. El puerto 8001 debe
 * coincidir con ENGINE_PORT del archivo .env. */
const { createApp } = Vue;

const ENGINE = location.protocol + "//" + location.hostname + ":8001";

createApp({
  data() {
    return {
      tab: "analyze",
      file: null,
      fileName: "",
      minLen: 4,
      dragover: false,
      loading: false,
      loadingMsg: "",
      error: "",
      result: null,
      stringQuery: "",
      samples: [],
      historyLoading: false,
      historyError: "",
      historyQuery: "",
      toast: "",
    };
  },

  computed: {
    entropy() {
      const e = this.result ? parseFloat(this.result.entropy) || 0 : 0;
      let cls = "lo", label = "Normal";
      if (e >= 7) { cls = "hi"; label = "Alta"; }
      else if (e >= 6) { cls = "mid"; label = "Elevada"; }
      return { cls: cls, label: label, pct: Math.min(e / 8 * 100, 100) };
    },
    filteredStrings() {
      if (!this.result) return [];
      const q = this.stringQuery.toLowerCase();
      if (!q) return this.result.strings;
      return this.result.strings.filter(s => s.toLowerCase().indexOf(q) > -1);
    },
    filteredSamples() {
      const q = this.historyQuery.toLowerCase();
      if (!q) return this.samples;
      return this.samples.filter(
        s => (s.filename + " " + s.sha256).toLowerCase().indexOf(q) > -1
      );
    },
  },

  methods: {
    fmtSize(b) {
      if (b < 1024) return b + " B";
      const u = ["KB", "MB", "GB"];
      let i = -1;
      do { b /= 1024; i++; } while (b >= 1024 && i < 2);
      return b.toFixed(1) + " " + u[i];
    },
    fmtDate(s) {
      return (s || "").replace("T", " ").slice(0, 19);
    },
    onPick(e) { this.setFile(e.target.files[0]); },
    onDrop(e) {
      this.dragover = false;
      this.setFile(e.dataTransfer.files[0]);
    },
    setFile(f) {
      if (f) { this.file = f; this.fileName = f.name; }
    },
    async api(path, opts) {
      let r;
      try {
        r = await fetch(ENGINE + path, opts);
      } catch (e) {
        throw new Error("No se pudo conectar con el engine (" + ENGINE + ").");
      }
      if (!r.ok) throw new Error("El engine respondió " + r.status + " en " + path);
      return r.json();
    },
    async fetchAll(sha) {
      const [hash, file, strings, entropy, ssdeep, exiftool, readelf] =
        await Promise.all([
          this.api("/samples/" + sha + "/hash"),
          this.api("/samples/" + sha + "/file"),
          this.api("/samples/" + sha + "/strings?min_len=" + this.minLen),
          this.api("/samples/" + sha + "/entropy"),
          this.api("/samples/" + sha + "/ssdeep"),
          this.api("/samples/" + sha + "/exiftool"),
          this.api("/samples/" + sha + "/readelf"),
        ]);
      return {
        hash: hash,
        file: file.file,
        strings: strings.strings,
        entropy: entropy.entropy,
        ssdeep: ssdeep.ssdeep,
        exiftool: exiftool,
        readelf: readelf.readelf,
      };
    },
    async analyze() {
      if (!this.file) { this.error = "Selecciona un archivo."; return; }
      this.error = "";
      this.result = null;
      this.loading = true;
      try {
        this.loadingMsg = "Subiendo la muestra…";
        const fd = new FormData();
        fd.append("file", this.file);
        const meta = await this.api("/samples", { method: "POST", body: fd });
        this.loadingMsg = "Ejecutando el análisis dentro del sandbox…";
        const a = await this.fetchAll(meta.sha256);
        this.result = Object.assign(
          { sha256: meta.sha256, filename: meta.filename, size: meta.size }, a
        );
        this.stringQuery = "";
      } catch (e) {
        this.error = e.message || "Error durante el análisis.";
      } finally {
        this.loading = false;
      }
    },
    async openSample(s) {
      this.tab = "analyze";
      this.error = "";
      this.result = null;
      this.loading = true;
      this.loadingMsg = "Cargando el análisis de la muestra…";
      try {
        const a = await this.fetchAll(s.sha256);
        this.result = Object.assign(
          { sha256: s.sha256, filename: s.filename, size: s.size }, a
        );
        this.stringQuery = "";
      } catch (e) {
        this.error = e.message || "No se pudo cargar la muestra.";
      } finally {
        this.loading = false;
      }
    },
    async loadHistory() {
      this.historyError = "";
      this.historyLoading = true;
      try {
        this.samples = await this.api("/samples");
      } catch (e) {
        this.historyError = e.message || "No se pudo cargar el historial.";
      } finally {
        this.historyLoading = false;
      }
    },
    go(tab) {
      this.tab = tab;
      if (tab === "history") this.loadHistory();
    },
    copy(text) {
      navigator.clipboard.writeText(text).then(
        () => this.flash("Copiado al portapapeles"),
        () => this.flash("No se pudo copiar")
      );
    },
    flash(msg) {
      this.toast = msg;
      clearTimeout(this._t);
      this._t = setTimeout(() => { this.toast = ""; }, 1900);
    },
  },

  template: `
<div>
  <header class="app-header">
    <div class="inner">
      <div class="app-title">Malware Lab <span>/ análisis estático</span></div>
      <nav class="tabs">
        <button class="tab" :class="{active: tab==='analyze'}" @click="go('analyze')">Analizar</button>
        <button class="tab" :class="{active: tab==='history'}" @click="go('history')">Historial</button>
      </nav>
    </div>
  </header>

  <main>
    <!-- ===================== ANALIZAR ===================== -->
    <div v-if="tab==='analyze'">
      <h2 class="page">Analizar muestra</h2>
      <p class="page-sub">Sube un binario para obtener su análisis estático.</p>

      <div class="alert error" v-if="error">{{ error }}</div>

      <div class="card">
        <div class="card-head">Nueva muestra</div>
        <div class="card-body">
          <div class="form-row">
            <label>Archivo</label>
            <div class="drop" :class="{over: dragover}"
                 @click="$refs.f.click()"
                 @dragover.prevent="dragover=true"
                 @dragleave.prevent="dragover=false"
                 @drop.prevent="onDrop">
              <input type="file" ref="f" @change="onPick">
              <div class="hint" v-if="!fileName">Haz clic para elegir un archivo o arrástralo aquí</div>
              <div class="picked" v-else>{{ fileName }}</div>
            </div>
          </div>
          <div class="form-row">
            <label>Longitud mínima de strings</label>
            <input type="number" v-model.number="minLen" min="1" max="100">
          </div>
          <button class="btn" @click="analyze" :disabled="loading || !file">Analizar</button>
        </div>
      </div>

      <div class="card" v-if="loading">
        <div class="loading"><div class="spinner"></div><span>{{ loadingMsg }}</span></div>
      </div>

      <!-- resultado -->
      <div v-if="result && !loading">
        <div class="card">
          <div class="card-head">Resumen</div>
          <div class="card-body">
            <div class="fname">{{ result.filename }}</div>
            <div class="meta">
              <span>SHA-256 <b class="mono">{{ result.sha256 }}</b></span>
              <span>Tamaño <b>{{ fmtSize(result.size) }}</b></span>
              <span>Cadenas <b>{{ result.strings.length }}</b></span>
            </div>
          </div>
        </div>

        <div class="card">
          <div class="card-head">Hashes</div>
          <div class="card-body flush">
            <table class="kv">
              <tr v-for="(val, alg) in result.hash" :key="alg">
                <td class="k">{{ alg }}</td>
                <td>
                  <div class="copyable">
                    <span class="mono">{{ val }}</span>
                    <button class="copy-btn" @click="copy(val)">Copiar</button>
                  </div>
                </td>
              </tr>
            </table>
          </div>
        </div>

        <div class="grid2">
          <div class="card">
            <div class="card-head">Tipo de archivo</div>
            <div class="card-body"><span class="mono">{{ result.file }}</span></div>
          </div>
          <div class="card">
            <div class="card-head">Entropía</div>
            <div class="card-body">
              <div class="ent-top">
                <span class="ent-num">{{ result.entropy }}</span>
                <span class="ent-unit">bits / byte</span>
                <span class="ent-tag" :class="entropy.cls">{{ entropy.label }}</span>
              </div>
              <div class="ent-bar">
                <div class="ent-fill" :class="entropy.cls" :style="{width: entropy.pct + '%'}"></div>
              </div>
              <div class="ent-note">Escala 0–8. Por encima de 7 sugiere empaquetado o cifrado.</div>
            </div>
          </div>
        </div>

        <div class="card">
          <div class="card-head">SSDeep</div>
          <div class="card-body">
            <div class="copyable">
              <span class="mono">{{ result.ssdeep }}</span>
              <button class="copy-btn" @click="copy(result.ssdeep)">Copiar</button>
            </div>
          </div>
        </div>

        <div class="card">
          <div class="card-head">ExifTool</div>
          <div class="card-body flush">
            <table class="kv">
              <tr v-for="(val, key) in result.exiftool" :key="key">
                <td class="k">{{ key }}</td>
                <td class="mono">{{ val }}</td>
              </tr>
            </table>
          </div>
        </div>

        <div class="card">
          <div class="card-head">ReadELF</div>
          <div class="card-body">
            <details>
              <summary>Mostrar cabeceras ELF</summary>
              <pre class="code">{{ result.readelf }}</pre>
            </details>
          </div>
        </div>

        <div class="card">
          <div class="card-head">Strings
            <span class="sub">{{ filteredStrings.length }} de {{ result.strings.length }}</span>
          </div>
          <div class="card-body">
            <input class="search" type="text" v-model="stringQuery" placeholder="Filtrar cadenas">
            <div class="str-list">
              <div class="srow" v-for="(s, i) in filteredStrings" :key="i">{{ s }}</div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- ===================== HISTORIAL ===================== -->
    <div v-if="tab==='history'">
      <h2 class="page">Historial</h2>
      <p class="page-sub">Muestras analizadas, almacenadas en la base de datos.</p>

      <div class="alert error" v-if="historyError">{{ historyError }}</div>

      <div class="card">
        <div class="card-head">Muestras <span class="sub">{{ filteredSamples.length }}</span></div>
        <div class="card-body" :class="{flush: !historyLoading && samples.length}">
          <div class="loading" v-if="historyLoading">
            <div class="spinner"></div><span>Cargando historial…</span>
          </div>
          <div class="empty" v-else-if="!samples.length">Aún no hay muestras analizadas.</div>
          <template v-else>
            <div style="padding:14px 14px 0">
              <input class="search" type="text" v-model="historyQuery"
                     placeholder="Filtrar por nombre o hash">
            </div>
            <table class="data">
              <thead>
                <tr><th>SHA-256</th><th>Archivo</th><th>Tamaño</th><th>Subida</th></tr>
              </thead>
              <tbody>
                <tr v-for="s in filteredSamples" :key="s.sha256" @click="openSample(s)">
                  <td class="mono">{{ s.sha256.slice(0, 28) }}…</td>
                  <td>{{ s.filename }}</td>
                  <td>{{ fmtSize(s.size) }}</td>
                  <td>{{ fmtDate(s.uploaded_at) }}</td>
                </tr>
              </tbody>
            </table>
            <div class="empty" v-if="!filteredSamples.length">Ninguna muestra coincide con el filtro.</div>
          </template>
        </div>
      </div>
    </div>
  </main>

  <footer class="foot">Malware Lab · análisis estático de binarios</footer>
  <div class="toast" v-if="toast">{{ toast }}</div>
</div>
`,
}).mount("#app");
