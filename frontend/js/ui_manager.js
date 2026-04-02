/* ==================================================================
   ui_manager.js — DOM helpers, toast notifications, form reading,
   version list updates, etc.
   ================================================================== */

const UI = (() => {

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
    const btnRebal  = document.getElementById("btn-rebalance");
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
      `${i + 1}. ${r.flight_code}  profit=$${r.profitability.toFixed(2)}  depth=${r.depth}`
    ).join("\n");
  }

  /* ---- BST modal ---- */

  function showBSTComparison(bst) {
    const modal = document.getElementById("bst-modal");
    const box   = document.getElementById("bst-comparison");
    modal.classList.remove("hidden");
    box.innerHTML = `
      <p><strong>BST height:</strong> ${bst.height}  |  <strong>Nodes:</strong> ${bst.size}</p>
      <p><strong>In-order:</strong></p>
      <pre style="max-height:200px;overflow:auto">${
        (bst.in_order || []).map(n => n.flight_code).join(" → ")
      }</pre>
    `;
  }
  function hideBSTModal() {
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
    showProfitability, showBSTComparison, hideBSTModal,
    downloadJSON,
  };
})();
