/* ==================================================================
   ui_manager.js - DOM helpers, toast notifications, form reading,
   version list updates, comparison modal and trace playback.
   ================================================================== */

const UI = (() => {
  let comparisonState = null;
  let activeTrace = null;
  let activeTraceIndex = 0;
  let activeTraceTimer = null;
  let lastTraceId = null;
  let stableTreeState = null;

  /* ---- toast ---- */

  function toast(msg, type = "info", ms = 3500) {
    const c = document.getElementById("toast-container");
    const t = document.createElement("div");
    t.className = `toast ${type}`;
    t.textContent = msg;
    c.appendChild(t);
    setTimeout(() => t.remove(), ms);
  }

  /* ---- form helpers ---- */

  function readFlightForm() {
    const f = document.getElementById("flight-form");
    const fd = new FormData(f);
    const data = {};
    for (const [k, v] of fd.entries()) {
      if (k === "alerts") {
        data[k] = v ? v.split(",").map(s => s.trim()).filter(Boolean) : [];
      } else if (["base_price", "promotion"].includes(k)) {
        data[k] = parseFloat(v) || 0;
      } else if (["passengers", "priority"].includes(k)) {
        data[k] = parseInt(v, 10) || 0;
      } else {
        data[k] = v.trim();
      }
    }
    return data;
  }

  function clearFlightForm() {
    document.getElementById("flight-form").reset();
  }

  function getDeleteCode() {
    return document.getElementById("delete-code").value.trim();
  }

  function getVersionName() {
    return document.getElementById("version-name").value.trim();
  }

  function getSelectedVersion() {
    const sel = document.getElementById("version-list");
    return sel.value || null;
  }

  function getCriticalDepth() {
    return parseInt(document.getElementById("critical-depth").value, 10) || 5;
  }

  /* ---- version list ---- */

  function updateVersionList(versions) {
    const sel = document.getElementById("version-list");
    sel.innerHTML = "";
    (versions || []).forEach(v => {
      const opt = document.createElement("option");
      opt.value = v.name;
      opt.textContent = `${v.name}  (${v.timestamp.slice(0, 19)})`;
      sel.appendChild(opt);
    });
  }

  /* ---- queue info ---- */

  function updateQueueInfo(status) {
    const box = document.getElementById("queue-info");
    if (!box) return;
    if (!status || status.size === 0) {
      box.textContent = "Cola vacía";
      return;
    }
    box.textContent = `Pendientes: ${status.size}\n` +
      (status.pending || []).map(r => r.flight_data.flight_code).join(", ");
  }

  /* ---- stress UI ---- */

  function setStressUI(isStress) {
    const badge = document.getElementById("stress-badge");
    const btnToggle = document.getElementById("btn-toggle-stress");
    const btnRebal = document.getElementById("btn-rebalance");
    if (isStress) {
      badge.classList.remove("hidden");
      btnToggle.textContent = "Desactivar estrés";
      btnRebal.disabled = false;
    } else {
      badge.classList.add("hidden");
      btnToggle.textContent = "Activar estrés";
      btnRebal.disabled = true;
    }
  }

  /* ---- undo button ---- */

  function setUndoEnabled(canUndo) {
    document.getElementById("btn-undo").disabled = !canUndo;
  }

  /* ---- audit ---- */

  function showAudit(report) {
    const sec = document.getElementById("audit-section");
    const pre = document.getElementById("audit-result");
    sec.style.display = "";
    pre.textContent = JSON.stringify(report, null, 2);
  }

  /* ---- profitability ---- */

  function showProfitability(ranking) {
    const box = document.getElementById("profitability-list");
    if (!ranking || ranking.length === 0) {
      box.textContent = "(sin datos)";
      return;
    }
    box.textContent = ranking.map((r, i) =>
      `${i + 1}. ${r.flight_code}  rentabilidad=$${r.profitability.toFixed(2)}  profundidad=${r.depth}`
    ).join("\n");
  }

  /* ---- operation trace ---- */

  function initOperationTrace() {
    const prev = document.getElementById("btn-trace-prev");
    const play = document.getElementById("btn-trace-play");
    const next = document.getElementById("btn-trace-next");
    const close = document.getElementById("btn-trace-close");
    if (!prev || !play || !next || !close) return;

    prev.addEventListener("click", () => _moveOperationTrace(-1));
    next.addEventListener("click", () => _moveOperationTrace(1));
    play.addEventListener("click", _toggleOperationTracePlayback);
    close.addEventListener("click", () => closeOperationTrace());
  }

  function syncOperationTrace(trace, finalTree) {
    stableTreeState = finalTree;

    if (!trace || !trace.steps || trace.steps.length === 0) {
      if (activeTrace) closeOperationTrace(true);
      return;
    }

    if (activeTrace && activeTrace.id === trace.id) {
      return;
    }

    if (!activeTrace && lastTraceId === trace.id) {
      return;
    }

    _openOperationTrace(trace, finalTree);
  }

  function _openOperationTrace(trace, finalTree) {
    const panel = document.getElementById("operation-trace-panel");
    if (!panel) return;

    stableTreeState = finalTree;
    activeTrace = trace;
    activeTraceIndex = 0;
    lastTraceId = trace.id;
    panel.classList.remove("hidden");
    _renderOperationTraceStep();
    _startOperationTracePlayback();
  }

  function closeOperationTrace(silent = false) {
    const panel = document.getElementById("operation-trace-panel");
    _stopOperationTracePlayback();
    activeTrace = null;
    activeTraceIndex = 0;
    if (panel) panel.classList.add("hidden");
    if (stableTreeState) TreeRenderer.render(stableTreeState);
    if (!silent) {
      const play = document.getElementById("btn-trace-play");
      if (play) play.textContent = "Reproducir";
    }
  }

  function _moveOperationTrace(delta) {
    if (!activeTrace) return;
    _stopOperationTracePlayback();
    const nextIndex = activeTraceIndex + delta;
    activeTraceIndex = Math.max(0, Math.min(nextIndex, activeTrace.steps.length - 1));
    _renderOperationTraceStep();
  }

  function _toggleOperationTracePlayback() {
    if (!activeTrace) return;
    if (activeTraceTimer) {
      _stopOperationTracePlayback();
      return;
    }
    _startOperationTracePlayback();
  }

  function _startOperationTracePlayback() {
    if (!activeTrace || activeTrace.steps.length <= 1) {
      _setPlaybackLabel(false);
      return;
    }
    _stopOperationTracePlayback();
    _setPlaybackLabel(true);
    activeTraceTimer = setInterval(() => {
      if (!activeTrace || activeTraceIndex >= activeTrace.steps.length - 1) {
        _stopOperationTracePlayback();
        return;
      }
      activeTraceIndex += 1;
      _renderOperationTraceStep();
      if (activeTraceIndex >= activeTrace.steps.length - 1) {
        _stopOperationTracePlayback();
      }
    }, 1400);
  }

  function _stopOperationTracePlayback() {
    if (activeTraceTimer) {
      clearInterval(activeTraceTimer);
      activeTraceTimer = null;
    }
    _setPlaybackLabel(false);
  }

  function _setPlaybackLabel(isPlaying) {
    const play = document.getElementById("btn-trace-play");
    if (play) play.textContent = isPlaying ? "Pausar" : "Reproducir";
  }

  function _renderOperationTraceStep() {
    if (!activeTrace) return;
    const step = activeTrace.steps[activeTraceIndex];
    const title = document.getElementById("operation-trace-title");
    const detail = document.getElementById("operation-trace-detail");
    const counter = document.getElementById("operation-trace-counter");
    const prev = document.getElementById("btn-trace-prev");
    const next = document.getElementById("btn-trace-next");

    if (title) {
      title.textContent = `${_traceActionLabel(activeTrace.action)}: ${activeTrace.target}`;
    }
    if (detail) {
      detail.textContent = `${step.title}. ${step.detail}`;
    }
    if (counter) {
      counter.textContent = `Paso ${activeTraceIndex + 1} de ${activeTrace.steps.length}`;
    }
    if (prev) prev.disabled = activeTraceIndex === 0;
    if (next) next.disabled = activeTraceIndex >= activeTrace.steps.length - 1;

    TreeRenderer.render(step.tree, {
      highlightCodes: step.highlight_codes || [],
    });
  }

  function _traceActionLabel(action) {
    return {
      insert: "Proceso de inserción",
      delete: "Proceso de eliminación",
    }[action] || "Proceso del árbol";
  }

  /* ---- BST modal ---- */

  function _comparisonNotes(comparison) {
    const notes = [];
    if (typeof comparison.height_advantage === "number") {
      if (comparison.height_advantage > 0) {
        notes.push(`El AVL reduce la altura en ${comparison.height_advantage} nivel(es).`);
      } else if (comparison.height_advantage === 0) {
        notes.push("Ambos árboles terminaron con la misma altura.");
      } else {
        notes.push(`El BST quedó ${Math.abs(comparison.height_advantage)} nivel(es) más bajo que el AVL.`);
      }
    }
    if (comparison.root_changed) {
      notes.push("La raíz cambió por efecto del rebalanceo AVL.");
    }
    if (comparison.same_in_order) {
      notes.push("El recorrido in-order se conserva porque ambos árboles almacenan el mismo conjunto ordenado.");
    }
    return notes;
  }

  function _renderComparisonCard(title, tree, tone) {
    const inOrder = (tree.in_order || []).map(n => n.flight_code).join(" &rarr; ") || "(vacío)";
    const rootLabel = tree.root
      ? `${tree.root.flight_code} &middot; ${tree.root.origin} &rarr; ${tree.root.destination}`
      : "Árbol vacío";
    const buttonLabel = tone === "avl" ? "Ver árbol AVL" : "Ver árbol BST";

    return `
      <article class="comparison-card ${tone}">
        <header>
          <h3>${title}</h3>
          <p class="comparison-root">${rootLabel}</p>
        </header>
        <div class="comparison-actions">
          <button type="button" class="comparison-visualize-btn" data-tree-target="${tone}">
            ${buttonLabel}
          </button>
        </div>
        <div class="comparison-stats">
          <div class="comparison-stat">
            <span>Raíz</span>
            <strong>${tree.root_code || "&mdash;"}</strong>
          </div>
          <div class="comparison-stat">
            <span>Altura</span>
            <strong>${tree.height}</strong>
          </div>
          <div class="comparison-stat">
            <span>Nodos</span>
            <strong>${tree.size}</strong>
          </div>
          <div class="comparison-stat">
            <span>Hojas</span>
            <strong>${tree.leaf_count}</strong>
          </div>
        </div>
        <div class="comparison-block">
          <p><strong>Recorrido in-order</strong></p>
          <pre class="comparison-pre">${inOrder}</pre>
        </div>
      </article>
    `;
  }

  function initComparisonModal() {
    const box = document.getElementById("bst-comparison");
    if (!box) return;

    box.addEventListener("click", (event) => {
      const button = event.target.closest(".comparison-visualize-btn");
      if (!button || !comparisonState) return;
      _showComparisonTree(button.dataset.treeTarget);
    });
  }

  function _showComparisonTree(kind) {
    const treeSummary = comparisonState?.[kind];
    const preview = document.getElementById("comparison-tree-preview");
    const title = document.getElementById("comparison-preview-title");
    const subtitle = document.getElementById("comparison-preview-subtitle");
    const svg = document.getElementById("comparison-tree-svg");
    const empty = document.getElementById("comparison-tree-empty");

    if (!treeSummary || !preview || !title || !subtitle || !svg) return;

    const names = {
      avl: "Visualización AVL balanceado",
      bst: "Visualización BST sin balanceo",
    };

    title.textContent = names[kind] || "Visualización del árbol";
    subtitle.textContent = treeSummary.root
      ? `Raíz ${treeSummary.root_code} • Altura ${treeSummary.height} • ${treeSummary.size} nodos`
      : "Árbol vacío";

    preview.classList.remove("hidden");
    TreeRenderer.renderPreview(treeSummary.tree, svg, empty);

    document
      .querySelectorAll(".comparison-visualize-btn")
      .forEach(btn => btn.classList.toggle("active", btn.dataset.treeTarget === kind));
  }

  function showBSTComparison(comparison) {
    const modal = document.getElementById("bst-modal");
    const box = document.getElementById("bst-comparison");
    modal.classList.remove("hidden");
    comparisonState = comparison;

    if (!comparison?.avl || !comparison?.bst) {
      const bst = comparison?.bst || comparison;
      box.innerHTML = `
        <p><strong>Altura BST:</strong> ${bst.height} | <strong>Nodos:</strong> ${bst.size}</p>
        <p><strong>Recorrido in-order:</strong></p>
        <pre class="comparison-pre">${(bst.in_order || []).map(n => n.flight_code).join(" &rarr; ")}</pre>
      `;
      return;
    }

    const notes = _comparisonNotes(comparison);
    box.innerHTML = `
      <div class="comparison-overview">
        <span class="comparison-chip">Raíz AVL: ${comparison.avl.root_code || "&mdash;"}</span>
        <span class="comparison-chip">Raíz BST: ${comparison.bst.root_code || "&mdash;"}</span>
        <span class="comparison-chip">&Delta; altura: ${comparison.height_advantage}</span>
        <span class="comparison-chip">&Delta; hojas: ${comparison.leaf_difference}</span>
      </div>
      <div class="comparison-grid">
        ${_renderComparisonCard("AVL balanceado", comparison.avl, "avl")}
        ${_renderComparisonCard("BST sin balanceo", comparison.bst, "bst")}
      </div>
      <section id="comparison-tree-preview" class="comparison-preview hidden">
        <div class="comparison-preview-head">
          <div>
            <h3 id="comparison-preview-title">Visualización del árbol</h3>
            <p id="comparison-preview-subtitle">Selecciona un botón para inspeccionar la estructura.</p>
          </div>
        </div>
        <div class="comparison-preview-canvas">
          <svg id="comparison-tree-svg"></svg>
          <p id="comparison-tree-empty">No hay nodos para visualizar.</p>
        </div>
      </section>
      <div class="comparison-block comparison-notes">
        <p><strong>Lectura rápida</strong></p>
        <ul>${notes.map(note => `<li>${note}</li>`).join("")}</ul>
      </div>
    `;
  }

  function hideBSTModal() {
    comparisonState = null;
    document.getElementById("bst-modal").classList.add("hidden");
  }

  /* ---- file download helper ---- */

  function downloadJSON(data, filename) {
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = filename;
    a.click();
    URL.revokeObjectURL(a.href);
  }

  return {
    toast, readFlightForm, clearFlightForm,
    getDeleteCode, getVersionName, getSelectedVersion,
    getCriticalDepth, updateVersionList, updateQueueInfo,
    setStressUI, setUndoEnabled, showAudit,
    showProfitability, initOperationTrace, syncOperationTrace,
    initComparisonModal, showBSTComparison, hideBSTModal,
    closeOperationTrace, downloadJSON,
  };
})();
