/* ==================================================================
   app.js - main coordinator. Wires buttons to API and refresh cycle.
   ================================================================== */

(function () {
  "use strict";

  let currentTraversal = "bfs";
  let traversalCache = null;
  let stressMode = false;

  async function refresh() {
    try {
      const state = await API.getTree();

      TreeRenderer.render(state.tree);
      MetricsDashboard.update(state.metrics);
      UI.setUndoEnabled(state.can_undo);
      UI.syncOperationTrace(state.operation_trace, state.tree);

      stressMode = state.metrics.stress_mode;
      UI.setStressUI(stressMode);

      document.getElementById("critical-depth").value = state.critical_depth;

      traversalCache = await API.getTraversals();
      MetricsDashboard.showTraversal(currentTraversal, traversalCache);

      const qs = await API.queueStatus();
      UI.updateQueueInfo(qs);

      const versions = await API.listVersions();
      UI.updateVersionList(versions);
    } catch (e) {
      console.error("refresh:", e);
    }
  }

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

  document.addEventListener("DOMContentLoaded", () => {
    TreeRenderer.init();
    UI.initOperationTrace();
    UI.initComparisonModal();

    document.getElementById("btn-load").addEventListener("click", async () => {
      const fileInput = document.getElementById("file-input");
      if (!fileInput.files.length) return UI.toast("Selecciona un archivo JSON", "error");
      const text = await fileInput.files[0].text();
      let data;
      try {
        data = JSON.parse(text);
      } catch {
        return UI.toast("JSON inv\u00e1lido", "error");
      }

      try {
        const result = await API.loadJSON(data);
        await refresh();
        UI.toast("\u00c1rbol cargado", "success");
        if (result.comparison) UI.showBSTComparison(result.comparison);
        else if (result.bst) UI.showBSTComparison(result.bst);
        else UI.hideBSTModal();
      } catch (e) {
        UI.toast(e.message, "error");
      }
    });

    document.getElementById("btn-export").addEventListener("click", async () => {
      try {
        const data = await API.exportTree();
        UI.downloadJSON(data, "skybalance_export.json");
        UI.toast("Exportado", "success");
      } catch (e) {
        UI.toast(e.message, "error");
      }
    });

    document.getElementById("flight-form").addEventListener("submit", async (e) => {
      e.preventDefault();
      const data = UI.readFlightForm();
      await act(() => API.createFlight(data), `Vuelo ${data.flight_code} insertado`);
      UI.clearFlightForm();
    });

    document.getElementById("btn-modify").addEventListener("click", async () => {
      const data = UI.readFlightForm();
      if (!data.flight_code) return UI.toast("Ingresa el c\u00f3digo", "error");
      await act(() => API.modifyFlight(data.flight_code, data), `Vuelo ${data.flight_code} modificado`);
    });

    document.getElementById("btn-delete").addEventListener("click", async () => {
      const code = UI.getDeleteCode();
      if (!code) return UI.toast("Ingresa c\u00f3digo a eliminar", "error");
      await act(() => API.deleteFlight(code), `Vuelo ${code} eliminado`);
    });

    document.getElementById("btn-cancel").addEventListener("click", async () => {
      const code = UI.getDeleteCode();
      if (!code) return UI.toast("Ingresa c\u00f3digo a cancelar", "error");
      await act(() => API.cancelFlight(code), `Sub-\u00e1rbol de ${code} cancelado`);
    });

    document.getElementById("btn-undo").addEventListener("click", () =>
      act(() => API.undo(), "Acci\u00f3n deshecha")
    );

    document.getElementById("btn-smart-delete").addEventListener("click", async () => {
      try {
        const res = await API.smartDelete();
        await refresh();
        UI.toast(`Eliminado ${res.target} (${res.count} nodos, rentabilidad=${res.profitability.toFixed(2)})`, "success");
      } catch (e) {
        UI.toast(e.message, "error");
      }
    });

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

    document.getElementById("btn-save-version").addEventListener("click", async () => {
      const name = UI.getVersionName();
      if (!name) return UI.toast("Nombre requerido", "error");
      await act(() => API.saveVersion(name), `Versi\u00f3n "${name}" guardada`);
    });

    document.getElementById("btn-restore-version").addEventListener("click", async () => {
      const name = UI.getSelectedVersion();
      if (!name) return UI.toast("Selecciona una versi\u00f3n", "error");
      await act(() => API.restoreVersion(name), `Versi\u00f3n "${name}" restaurada`);
    });

    document.getElementById("btn-toggle-stress").addEventListener("click", () =>
      act(() => API.toggleStress(), stressMode ? "Estr\u00e9s desactivado" : "Estr\u00e9s activado")
    );

    document.getElementById("btn-rebalance").addEventListener("click", async () => {
      try {
        const report = await API.rebalance();
        await refresh();
        UI.toast(
          `Rebalanceo: ${report.total_rotations} rotaciones, altura ${report.initial_height}\u2192${report.final_height}`,
          "success"
        );
      } catch (e) {
        UI.toast(e.message, "error");
      }
    });

    document.getElementById("btn-audit").addEventListener("click", async () => {
      try {
        const report = await API.audit();
        UI.showAudit(report);
        UI.toast(report.summary, report.is_valid ? "success" : "error");
      } catch (e) {
        UI.toast(e.message, "error");
      }
    });

    document.getElementById("btn-set-depth").addEventListener("click", async () => {
      const d = UI.getCriticalDepth();
      await act(() => API.setDepth(d), `Profundidad cr\u00edtica = ${d}`);
    });

    document.getElementById("btn-profitability").addEventListener("click", async () => {
      try {
        const ranking = await API.getProfitability();
        UI.showProfitability(ranking);
      } catch (e) {
        UI.toast(e.message, "error");
      }
    });

    document.querySelectorAll(".tab[data-trav]").forEach(btn => {
      btn.addEventListener("click", () => {
        document.querySelectorAll(".tab").forEach(t => t.classList.remove("active"));
        btn.classList.add("active");
        currentTraversal = btn.dataset.trav;
        if (traversalCache) MetricsDashboard.showTraversal(currentTraversal, traversalCache);
      });
    });

    document.getElementById("btn-zoom-in").addEventListener("click", TreeRenderer.zoomIn);
    document.getElementById("btn-zoom-out").addEventListener("click", TreeRenderer.zoomOut);
    document.getElementById("btn-zoom-reset").addEventListener("click", TreeRenderer.zoomReset);

    document.getElementById("btn-close-bst").addEventListener("click", UI.hideBSTModal);

    refresh();
  });
})();
