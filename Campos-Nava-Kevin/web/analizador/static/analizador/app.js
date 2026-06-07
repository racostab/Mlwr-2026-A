/* ============================================================
   Malware Lab — interactividad (vanilla JS, sin dependencias)
   Mejora progresiva: la página funciona sin este script.
   ============================================================ */
(function () {
  'use strict';

  /* ---- 1. Dropzone: arrastrar y soltar ---- */
  var dz = document.querySelector('[data-dropzone]');
  if (dz) {
    var input = dz.querySelector('[data-dropzone-input]');
    var nameEl = dz.querySelector('[data-dropzone-name]');

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

  /* ---- 9. Modo de análisis: muestra/oculta los extras ---- */
  var modeRadios = document.querySelectorAll('[data-mode]');
  var customPanels = document.querySelectorAll('[data-custom-panel]');
  if (modeRadios.length && customPanels.length) {
    var syncMode = function () {
      var custom = false;
      Array.prototype.forEach.call(modeRadios, function (r) {
        if (r.checked && r.value === 'custom') custom = true;
      });
      Array.prototype.forEach.call(customPanels, function (p) {
        p.classList.toggle('is-visible', custom);
      });
    };
    Array.prototype.forEach.call(modeRadios, function (r) {
      r.addEventListener('change', syncMode);
    });
    syncMode();
  }

  /* ---- 10. Barra para añadir comandos personalizados (chips) ----
     Sin JS, el usuario escribe en el textarea de respaldo (uno por línea).
     Con JS, escribe en la barra y cada comando se vuelve un chip; el textarea
     queda oculto y se rellena con los chips (separados por salto de línea), que
     es lo que el backend espera en `cmd_libre`. */
  var cmdInput = document.querySelector('[data-cmd-input]');
  var cmdAdd = document.querySelector('[data-cmd-add]');
  var cmdChips = document.querySelector('[data-cmd-chips]');
  var cmdStore = document.querySelector('[data-cmd-store]');
  if (cmdInput && cmdChips && cmdStore) {
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

    // Con JS activo el textarea es solo almacén: arranca vacío.
    cmdStore.value = '';
  }
})();
