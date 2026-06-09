/* ============================================================
   Malware Lab — interactividad (vanilla JS, sin dependencias)
   Mejora progresiva: la página funciona sin este script.
   ============================================================ */
(function () {
  'use strict';

  /* ---- 1. Experimentos: cada bloque es independiente ----
     Un "experimento" agrupa N muestras + sus comandos. Cada bloque trae su
     propio dropzone, su toggle de modo y su barra de comandos. El usuario puede
     añadir más experimentos (se clona el molde y se reindexan los campos:
     file_0, mode_0… → file_1, mode_1…) o quitarlos. */

  function initDropzone(dz) {
    if (!dz || dz.dataset.ready) return;
    dz.dataset.ready = '1';
    var input = dz.querySelector('[data-dropzone-input]');
    var nameEl = dz.querySelector('[data-dropzone-name]');
    if (!input) return;

    function reflectFile() {
      if (input.files && input.files.length) {
        var count = input.files.length;
        nameEl.textContent = count === 1
          ? input.files[0].name
          : count + ' archivos seleccionados';
        nameEl.hidden = false;
        dz.classList.add('has-file');
      } else {
        nameEl.hidden = true;
        dz.classList.remove('has-file');
      }
    }
    input.addEventListener('change', reflectFile);

    ['dragenter', 'dragover'].forEach(function (ev) {
      dz.addEventListener(ev, function (e) {
        e.preventDefault();
        dz.classList.add('is-dragover');
      });
    });
    ['dragleave', 'drop'].forEach(function (ev) {
      dz.addEventListener(ev, function (e) {
        e.preventDefault();
        if (ev === 'drop' || !dz.contains(e.relatedTarget)) {
          dz.classList.remove('is-dragover');
        }
      });
    });
    dz.addEventListener('drop', function (e) {
      if (e.dataTransfer && e.dataTransfer.files.length) {
        input.files = e.dataTransfer.files;
        reflectFile();
      }
    });
  }

  function initMode(block) {
    var radios = block.querySelectorAll('[data-mode]');
    var panel = block.querySelector('[data-custom-panel]');
    if (!radios.length || !panel) return;
    var sync = function () {
      var custom = false;
      Array.prototype.forEach.call(radios, function (r) {
        if (r.checked && r.value === 'custom') custom = true;
      });
      panel.classList.toggle('is-visible', custom);
    };
    Array.prototype.forEach.call(radios, function (r) {
      r.addEventListener('change', sync);
    });
    sync();
  }

  function initCmd(block) {
    var cmdInput = block.querySelector('[data-cmd-input]');
    var cmdAdd = block.querySelector('[data-cmd-add]');
    var cmdChips = block.querySelector('[data-cmd-chips]');
    var cmdStore = block.querySelector('[data-cmd-store]');
    if (!cmdInput || !cmdChips || !cmdStore) return;

    var syncStore = function () {
      var vals = Array.prototype.map.call(
        cmdChips.querySelectorAll('[data-cmd-value]'),
        function (el) { return el.getAttribute('data-cmd-value'); }
      );
      cmdStore.value = vals.join('\n');
    };
    var addCmd = function () {
      var v = cmdInput.value.trim();
      if (!v) return;
      var li = document.createElement('li');
      li.className = 'chip';
      li.setAttribute('data-cmd-value', v);

      var txt = document.createElement('span');
      txt.className = 'chip__text mono';
      txt.textContent = v;

      var rm = document.createElement('button');
      rm.type = 'button';
      rm.className = 'chip__remove';
      rm.setAttribute('aria-label', 'Quitar comando');
      rm.innerHTML = '&times;';

      li.appendChild(txt);
      li.appendChild(rm);
      cmdChips.appendChild(li);
      cmdInput.value = '';
      cmdInput.focus();
      syncStore();
    };

    if (cmdAdd) cmdAdd.addEventListener('click', addCmd);
    cmdInput.addEventListener('keydown', function (e) {
      if (e.key === 'Enter') { e.preventDefault(); addCmd(); }
    });
    cmdChips.addEventListener('click', function (e) {
      var btn = e.target.closest('.chip__remove');
      if (!btn) return;
      btn.parentNode.remove();
      syncStore();
    });

    // Con JS activo el textarea es solo almacén: parte de los chips actuales.
    syncStore();
  }

  function initExperiment(block) {
    initDropzone(block.querySelector('[data-dropzone]'));
    initMode(block);
    initCmd(block);
  }

  var wrap = document.querySelector('[data-experiments]');
  if (wrap) {
    var blocks = function () {
      return Array.prototype.slice.call(wrap.querySelectorAll('[data-experiment]'));
    };

    // Reasigna los names sufijados (file_0, mode_0…) según la posición y
    // actualiza la etiqueta y la visibilidad del botón de quitar.
    var reindex = function () {
      var bs = blocks();
      bs.forEach(function (block, i) {
        Array.prototype.forEach.call(
          block.querySelectorAll('[data-field]'),
          function (el) { el.name = el.getAttribute('data-field') + '_' + i; }
        );
        var label = block.querySelector('[data-experiment-label]');
        if (label) label.textContent = 'Experimento ' + (i + 1);
      });
      bs.forEach(function (block) {
        var rm = block.querySelector('[data-experiment-remove]');
        if (rm) rm.hidden = bs.length <= 1;
      });
    };

    // Deja un bloque clonado en limpio (sin archivos, modo por defecto, sin chips).
    var resetBlock = function (block) {
      var dz = block.querySelector('[data-dropzone]');
      if (dz) {
        dz.removeAttribute('data-ready');
        dz.classList.remove('has-file', 'is-dragover');
        var nm = dz.querySelector('[data-dropzone-name]');
        if (nm) { nm.hidden = true; nm.textContent = ''; }
      }
      var fileInput = block.querySelector('[data-dropzone-input]');
      if (fileInput) fileInput.value = '';
      Array.prototype.forEach.call(block.querySelectorAll('[data-mode]'), function (r) {
        r.checked = r.value === 'default';
      });
      Array.prototype.forEach.call(
        block.querySelectorAll('input[type="checkbox"]'),
        function (c) { c.checked = false; }
      );
      var ml = block.querySelector('[data-field="min_len"]');
      if (ml) ml.value = '4';
      var chips = block.querySelector('[data-cmd-chips]');
      if (chips) chips.innerHTML = '';
      var store = block.querySelector('[data-cmd-store]');
      if (store) store.value = '';
      var cmdIn = block.querySelector('[data-cmd-input]');
      if (cmdIn) cmdIn.value = '';
      var panel = block.querySelector('[data-custom-panel]');
      if (panel) panel.classList.remove('is-visible');
    };

    var addBtn = document.querySelector('[data-experiment-add]');
    if (addBtn) {
      addBtn.addEventListener('click', function () {
        var first = wrap.querySelector('[data-experiment]');
        if (!first) return;
        var clone = first.cloneNode(true);
        resetBlock(clone);
        wrap.appendChild(clone);
        reindex();
        initExperiment(clone);
        clone.scrollIntoView({ behavior: 'smooth', block: 'center' });
      });
    }

    wrap.addEventListener('click', function (e) {
      var rm = e.target.closest('[data-experiment-remove]');
      if (!rm) return;
      if (blocks().length <= 1) return;
      var block = rm.closest('[data-experiment]');
      if (block) block.remove();
      reindex();
    });

    blocks().forEach(initExperiment);
    reindex();
  }

  /* ---- 2. Overlay de carga al enviar el análisis ---- */
  var overlay = document.querySelector('[data-overlay]');
  var loadingForm = document.querySelector('[data-loading-form]');
  if (overlay && loadingForm) {
    loadingForm.addEventListener('submit', function () {
      if (loadingForm.checkValidity()) {
        overlay.classList.add('is-visible');
        overlay.setAttribute('aria-hidden', 'false');
      }
    });
  }

  /* ---- 3. Copiar al portapapeles ---- */
  document.addEventListener('click', function (e) {
    var btn = e.target.closest('[data-copy]');
    if (!btn) return;
    var text = btn.getAttribute('data-copy');

    var feedback = function () {
      btn.classList.add('is-copied');
      setTimeout(function () { btn.classList.remove('is-copied'); }, 1500);
    };

    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(feedback).catch(function () {});
    } else {
      var ta = document.createElement('textarea');
      ta.value = text;
      ta.style.position = 'fixed';
      ta.style.opacity = '0';
      document.body.appendChild(ta);
      ta.select();
      try { document.execCommand('copy'); feedback(); } catch (_) {}
      document.body.removeChild(ta);
    }
  });

  /* ---- 4. Pestañas del reporte (accesibles con teclado) ----
     Puede haber varios grupos de pestañas (un reporte por muestra),
     así que inicializamos cada [data-tabs] de forma independiente. */
  Array.prototype.forEach.call(
    document.querySelectorAll('[data-tabs]'),
    function (tabsRoot) {
      var tabs = Array.prototype.slice.call(tabsRoot.querySelectorAll('[data-tab]'));
      var panels = Array.prototype.slice.call(tabsRoot.querySelectorAll('[data-tab-panel]'));

      function activate(tab) {
        tabs.forEach(function (t) {
          var on = t === tab;
          t.classList.toggle('is-active', on);
          t.setAttribute('aria-selected', on ? 'true' : 'false');
          t.tabIndex = on ? 0 : -1;
        });
        panels.forEach(function (p) {
          p.classList.toggle('is-active', p.id === tab.getAttribute('aria-controls'));
        });
      }

      tabs.forEach(function (tab, i) {
        tab.addEventListener('click', function () { activate(tab); });
        tab.addEventListener('keydown', function (e) {
          var next = null;
          if (e.key === 'ArrowRight') next = (i + 1) % tabs.length;
          else if (e.key === 'ArrowLeft') next = (i - 1 + tabs.length) % tabs.length;
          else if (e.key === 'Home') next = 0;
          else if (e.key === 'End') next = tabs.length - 1;
          if (next !== null) {
            e.preventDefault();
            tabs[next].focus();
            activate(tabs[next]);
          }
        });
      });
    }
  );

  /* ---- 5. Medidor de entropía (uno por muestra) ---- */
  Array.prototype.forEach.call(
    document.querySelectorAll('[data-entropy]'),
    function (meter) {
      var value = parseFloat(meter.getAttribute('data-entropy'));
      if (isNaN(value)) return;
      var stat = meter.closest('.stat') || meter.parentNode;
      var note = stat ? stat.querySelector('[data-entropy-note]') : null;
      var pct = Math.max(0, Math.min(100, (value / 8) * 100));
      var fill = meter.querySelector('.meter__fill');
      var severity = value >= 7.2 ? 'is-danger' : (value >= 6 ? 'is-warn' : 'is-ok');
      meter.classList.add(severity);
      requestAnimationFrame(function () {
        if (fill) fill.style.width = pct.toFixed(1) + '%';
      });
      if (note) {
        note.textContent = value >= 7.2
          ? 'Entropía alta — posible empaquetado o cifrado'
          : (value >= 6 ? 'Entropía moderada' : 'Entropía normal para un binario');
        note.classList.add(severity);
      }
    }
  );

  /* ---- 6. Filtro de strings (uno por muestra) ---- */
  Array.prototype.forEach.call(
    document.querySelectorAll('[data-strings-filter]'),
    function (filter) {
      var scope = filter.closest('[data-tab-panel]') || document;
      var list = scope.querySelector('[data-strings-list]');
      var counter = scope.querySelector('[data-strings-count]');
      var lines = list ? Array.prototype.slice.call(list.children) : [];

      filter.addEventListener('input', function () {
        var q = filter.value.toLowerCase();
        var shown = 0;
        lines.forEach(function (li) {
          var match = li.textContent.toLowerCase().indexOf(q) !== -1;
          li.hidden = !match;
          if (match) shown++;
        });
        if (counter) counter.textContent = shown;
      });
    }
  );

  /* ---- 7. Formato de fechas ---- */
  Array.prototype.forEach.call(
    document.querySelectorAll('[data-datetime]'),
    function (el) {
      var d = new Date(el.getAttribute('data-datetime'));
      if (!isNaN(d.getTime())) {
        el.textContent = d.toLocaleString('es-MX', {
          year: 'numeric', month: 'short', day: '2-digit',
          hour: '2-digit', minute: '2-digit'
        });
      }
    }
  );

  /* ---- 8. Sidebar: drawer en móvil ---- */
  var sidebar = document.querySelector('[data-sidebar]');
  var sbToggle = document.querySelector('[data-sidebar-toggle]');
  var sbBackdrop = document.querySelector('[data-sidebar-backdrop]');
  if (sidebar && sbToggle && sbBackdrop) {
    var setSidebar = function (open) {
      sidebar.classList.toggle('is-open', open);
      sbBackdrop.classList.toggle('is-visible', open);
      sbToggle.setAttribute('aria-expanded', open ? 'true' : 'false');
      document.body.classList.toggle('no-scroll', open);
    };
    sbToggle.addEventListener('click', function () {
      setSidebar(!sidebar.classList.contains('is-open'));
    });
    sbBackdrop.addEventListener('click', function () { setSidebar(false); });
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape') setSidebar(false);
    });
    sidebar.addEventListener('click', function (e) {
      if (e.target.closest('a')) setSidebar(false);
    });
  }
})();
