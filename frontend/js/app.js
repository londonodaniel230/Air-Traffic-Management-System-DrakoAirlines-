/* ==================================================================
   app.js — main coordinator.  Wires buttons → API → refresh cycle.
   ================================================================== */

(function () {
  "use strict";

  let currentTraversal = "bfs";
  let traversalCache   = null;
  let stressMode       = false;

  /* ================================================================
     REFRESH — single function that syncs ALL panels with the server
     ================================================================ */

  async function refresh() {
    try {
      const state = await API.getTree();

      /* tree visualisation */
      TreeRenderer.render(state.tree);

      /* metrics panel */
      MetricsDashboard.update(state.metrics);

      /* undo button */
      UI.setUndoEnabled(state.can_undo);

      /* stress badge */
      stressMode = state.metrics.stress_mode;
      UI.setStressUI(stressMode);

      /* critical depth input */
      document.getElementById("critical-depth").value = state.critical_depth;

      /* traversals */
      traversalCache = await API.getTraversals();
      MetricsDashboard.showTraversal(currentTraversal, traversalCache);

      /* queue */
      const qs = await API.queueStatus();
      UI.updateQueueInfo(qs);

      /* versions */
      const versions = await API.listVersions();
      UI.updateVersionList(versions);
    } catch (e) {
      console.error("refresh:", e);
    }
  }

  /* helper — run action, refresh, show toast */
  async function act(fn, successMsg) {
    try {
      const result = await fn();
      await refresh();
      if (successMsg) UI.toast(successMsg, "success");
      return result;
    } catch (e) {
      UI.toast(e.message, "error");
      throw e;
    }
  }

  /* ================================================================
     EVENT WIRING
     ================================================================ */

  document.addEventListener("DOMContentLoaded", () => {
    TreeRenderer.init();

    /* ---- Load JSON ---- */
    document.getElementById("btn-load").addEventListener("click", async () => {
      const fileInput = document.getElementById("file-input");
      if (!fileInput.files.length) return UI.toast("Selecciona un archivo JSON", "error");
      const text = await fileInput.files[0].text();
      let data;
      try { data = JSON.parse(text); } catch { return UI.toast("JSON inválido", "error"); }
      try {
        const result = await API.loadJSON(data);
        await refresh();
        UI.toast("Árbol cargado", "success");
        if (result.bst) UI.showBSTComparison(result.bst);
      } catch (e) { UI.toast(e.message, "error"); }
    });

    document.getElementById("btn-export").addEventListener("click", async () => {
      try {
        const data = await API.exportTree();
        UI.downloadJSON(data, "skybalance_export.json");
        UI.toast("Exportado", "success");
      } catch (e) { UI.toast(e.message, "error"); }
    });

    /* ---- CRUD ---- */
    document.getElementById("flight-form").addEventListener("submit", async (e) => {
      e.preventDefault();
      const data = UI.readFlightForm();
      await act(() => API.createFlight(data), `Vuelo ${data.flight_code} insertado`);
      UI.clearFlightForm();
    });

    document.getElementById("btn-modify").addEventListener("click", async () => {
      const data = UI.readFlightForm();
      if (!data.flight_code) return UI.toast("Ingresa el código", "error");
      await act(() => API.modifyFlight(data.flight_code, data), `Vuelo ${data.flight_code} modificado`);
    });

    document.getElementById("btn-delete").addEventListener("click", async () => {
      const code = UI.getDeleteCode();
      if (!code) return UI.toast("Ingresa código a eliminar", "error");
      await act(() => API.deleteFlight(code), `Vuelo ${code} eliminado`);
    });

    document.getElementById("btn-cancel").addEventListener("click", async () => {
      const code = UI.getDeleteCode();
      if (!code) return UI.toast("Ingresa código a cancelar", "error");
      const res = await act(() => API.cancelFlight(code), `Sub-árbol de ${code} cancelado`);
    });

    /* ---- Undo ---- */
    document.getElementById("btn-undo").addEventListener("click", () =>
      act(() => API.undo(), "Acción deshecha")
    );

    /* ---- Smart delete ---- */
    document.getElementById("btn-smart-delete").addEventListener("click", async () => {
      try {
        const res = await API.smartDelete();
        await refresh();
        UI.toast(`Eliminado ${res.target} (${res.count} nodos, profit=${res.profitability.toFixed(2)})`, "success");
      } catch (e) { UI.toast(e.message, "error"); }
    });

    /* ---- Queue ---- */
    document.getElementById("btn-queue-add").addEventListener("click", async () => {
      const data = UI.readFlightForm();
      if (!data.flight_code) return UI.toast("Llena el formulario", "error");
      await act(() => API.queueAdd(data), `${data.flight_code} encolado`);
      UI.clearFlightForm();
    });

    document.getElementById("btn-queue-next").addEventListener("click", () =>
      act(() => API.queueNext(), "Siguiente procesado")
    );

    document.getElementById("btn-queue-all").addEventListener("click", () =>
      act(() => API.queueAll(), "Cola procesada")
    );

    /* ---- Versions ---- */
    document.getElementById("btn-save-version").addEventListener("click", async () => {
      const name = UI.getVersionName();
      if (!name) return UI.toast("Nombre requerido", "error");
      await act(() => API.saveVersion(name), `Versión "${name}" guardada`);
    });

    document.getElementById("btn-restore-version").addEventListener("click", async () => {
      const name = UI.getSelectedVersion();
      if (!name) return UI.toast("Selecciona una versión", "error");
      await act(() => API.restoreVersion(name), `Versión "${name}" restaurada`);
    });

    /* ---- Stress mode ---- */
    document.getElementById("btn-toggle-stress").addEventListener("click", () =>
      act(() => API.toggleStress(), stressMode ? "Estrés desactivado" : "Estrés activado")
    );

    document.getElementById("btn-rebalance").addEventListener("click", async () => {
      try {
        const report = await API.rebalance();
        await refresh();
        UI.toast(
          `Rebalanceo: ${report.total_rotations} rotaciones, ` +
          `altura ${report.initial_height}→${report.final_height}`,
          "success"
        );
      } catch (e) { UI.toast(e.message, "error"); }
    });

    /* ---- Audit ---- */
    document.getElementById("btn-audit").addEventListener("click", async () => {
      try {
        const report = await API.audit();
        UI.showAudit(report);
        UI.toast(report.summary, report.is_valid ? "success" : "error");
      } catch (e) { UI.toast(e.message, "error"); }
    });

    /* ---- Penalty ---- */
    document.getElementById("btn-set-depth").addEventListener("click", async () => {
      const d = UI.getCriticalDepth();
      await act(() => API.setDepth(d), `Profundidad crítica = ${d}`);
    });

    /* ---- Profitability ---- */
    document.getElementById("btn-profitability").addEventListener("click", async () => {
      try {
        const ranking = await API.getProfitability();
        UI.showProfitability(ranking);
      } catch (e) { UI.toast(e.message, "error"); }
    });

    /* ---- Traversal tabs ---- */
    document.querySelectorAll(".tab[data-trav]").forEach(btn => {
      btn.addEventListener("click", () => {
        document.querySelectorAll(".tab").forEach(t => t.classList.remove("active"));
        btn.classList.add("active");
        currentTraversal = btn.dataset.trav;
        if (traversalCache) MetricsDashboard.showTraversal(currentTraversal, traversalCache);
      });
    });

    /* ---- Zoom ---- */
    document.getElementById("btn-zoom-in").addEventListener("click",    TreeRenderer.zoomIn);
    document.getElementById("btn-zoom-out").addEventListener("click",   TreeRenderer.zoomOut);
    document.getElementById("btn-zoom-reset").addEventListener("click", TreeRenderer.zoomReset);

    /* ---- BST modal close ---- */
    document.getElementById("btn-close-bst").addEventListener("click", UI.hideBSTModal);

    /* ---- Initial state ---- */
    refresh();
  });
})();
