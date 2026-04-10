/* ==================================================================
   tree_renderer.js — draws the AVL tree as SVG inside #tree-svg.
   Uses an in-order index layout (x) and depth (y).
   ================================================================== */

const TreeRenderer = (() => {
  const NODE_R       = 26;
  const LEVEL_H      = 80;
  const NODE_GAP     = 58;
  const PAD          = 40;

  let scale = 1;
  let svg, container, tooltip;

  function init() {
    svg       = document.getElementById("tree-svg");
    container = document.getElementById("tree-container");
    tooltip   = document.getElementById("tree-node-tooltip");
  }

  /* ---- layout helpers ---- */

  function _positions(root) {
    let idx = 0;
    const pos = {};
    (function walk(n, depth) {
      if (!n) return;
      walk(n.left, depth + 1);
      pos[n.flight_code] = { x: PAD + idx * NODE_GAP, y: PAD + depth * LEVEL_H, data: n };
      idx++;
      walk(n.right, depth + 1);
    })(root, 0);
    return pos;
  }

  function _treeDepth(n) {
    if (!n) return 0;
    return 1 + Math.max(_treeDepth(n.left), _treeDepth(n.right));
  }

  function _countNodes(n) {
    if (!n) return 0;
    return 1 + _countNodes(n.left) + _countNodes(n.right);
  }

  /* ---- render ---- */

  function render(treeData, options = {}) {
    if (!svg) init();
    const emptyMsg = document.getElementById("tree-empty-msg");
    _renderInto(treeData, svg, emptyMsg, scale, options);
  }

  function renderPreview(treeData, svgElement, emptyElement, options = {}) {
    if (!svgElement) return;
    _renderInto(treeData, svgElement, emptyElement, 1, options);
  }

  function _renderInto(treeData, svgElement, emptyElement, targetScale = 1, options = {}) {
    const root = treeData && treeData.root ? treeData.root : null;
    const highlightCodes = new Set(options.highlightCodes || []);

    if (!root) {
      svgElement.innerHTML = "";
      svgElement.removeAttribute("viewBox");
      if (emptyElement) emptyElement.style.display = "";
      if (svgElement === svg) _hideTooltip();
      return;
    }
    if (emptyElement) emptyElement.style.display = "none";

    const pos   = _positions(root);
    const codes = Object.keys(pos);
    const maxX  = Math.max(...codes.map(c => pos[c].x)) + PAD + NODE_R;
    const maxY  = Math.max(...codes.map(c => pos[c].y)) + PAD + NODE_R + 30;

    svgElement.setAttribute("width",  maxX * targetScale);
    svgElement.setAttribute("height", maxY * targetScale);
    svgElement.setAttribute("viewBox", `0 0 ${maxX} ${maxY}`);

    let html = "";

    /* edges */
    (function drawEdges(n) {
      if (!n) return;
      const p = pos[n.flight_code];
      if (n.left) {
        const c = pos[n.left.flight_code];
        html += `<line class="tree-edge" x1="${p.x}" y1="${p.y}" x2="${c.x}" y2="${c.y}"/>`;
        drawEdges(n.left);
      }
      if (n.right) {
        const c = pos[n.right.flight_code];
        html += `<line class="tree-edge" x1="${p.x}" y1="${p.y}" x2="${c.x}" y2="${c.y}"/>`;
        drawEdges(n.right);
      }
    })(root);

    /* nodes */
    for (const code of codes) {
      const { x, y, data } = pos[code];
      const classes = ["tree-node"];
      if (data.is_critical) classes.push("critical");
      if (highlightCodes.has(code)) classes.push("highlighted");
      const cls = classes.join(" ");
      html += `<g class="${cls}" data-code="${code}">`;
      html += `<circle cx="${x}" cy="${y}" r="${NODE_R}"/>`;
      html += `<text x="${x}" y="${y - 4}">${code}</text>`;
      html += `<text class="node-bf" x="${x}" y="${y + 12}">BF ${data.balance_factor ?? "?"}</text>`;
      html += `</g>`;
    }

    svgElement.innerHTML = html;
    if (svgElement === svg) _bindTooltipEvents(svgElement, pos);
  }

  function _bindTooltipEvents(svgElement, pos) {
    if (!tooltip) return;

    svgElement.querySelectorAll(".tree-node").forEach(group => {
      const code = group.dataset.code;
      const nodeData = pos[code]?.data;
      if (!nodeData) return;

      group.addEventListener("mouseenter", (event) => {
        _showTooltip(nodeData, event);
      });
      group.addEventListener("mousemove", (event) => {
        _moveTooltip(event);
      });
      group.addEventListener("mouseleave", () => {
        _hideTooltip();
      });
    });
  }

  function _showTooltip(nodeData, event) {
    if (!tooltip) return;
    tooltip.innerHTML = _tooltipMarkup(nodeData);
    tooltip.classList.remove("hidden");
    _moveTooltip(event);
  }

  function _moveTooltip(event) {
    if (!tooltip || tooltip.classList.contains("hidden")) return;
    const pad = 16;
    const rect = tooltip.getBoundingClientRect();
    const maxLeft = window.innerWidth - rect.width - 8;
    const maxTop = window.innerHeight - rect.height - 8;
    const left = Math.min(event.clientX + pad, Math.max(8, maxLeft));
    const top = Math.min(event.clientY + pad, Math.max(8, maxTop));
    tooltip.style.left = `${left}px`;
    tooltip.style.top = `${top}px`;
  }

  function _hideTooltip() {
    if (!tooltip) return;
    tooltip.classList.add("hidden");
  }

  function _tooltipMarkup(nodeData) {
    const alerts = Array.isArray(nodeData.alerts) && nodeData.alerts.length
      ? nodeData.alerts.join(", ")
      : "Sin alertas";

    return `
      <h3>${_escape(nodeData.flight_code || "Nodo")}</h3>
      <div class="tree-tooltip-grid">
        <strong>Ruta</strong><span>${_escape(nodeData.origin || "—")} → ${_escape(nodeData.destination || "—")}</span>
        <strong>Salida</strong><span>${_escape(nodeData.departure_time || "No registrada")}</span>
        <strong>Precio base</strong><span>$${_formatNumber(nodeData.base_price)}</span>
        <strong>Precio final</strong><span>$${_formatNumber(nodeData.final_price)}</span>
        <strong>Pasajeros</strong><span>${_escape(nodeData.passengers)}</span>
        <strong>Promoción</strong><span>$${_formatNumber(nodeData.promotion)}</span>
        <strong>Penalidad</strong><span>$${_formatNumber(nodeData.penalty)}</span>
        <strong>Prioridad</strong><span>${_escape(nodeData.priority)}</span>
        <strong>Altura</strong><span>${_escape(nodeData.height)}</span>
        <strong>Balance</strong><span>${_escape(nodeData.balance_factor)}</span>
        <strong>Crítico</strong><span>${nodeData.is_critical ? "Sí" : "No"}</span>
      </div>
      <div class="tree-tooltip-alerts"><strong>Alertas:</strong> ${_escape(alerts)}</div>
    `;
  }

  function _formatNumber(value) {
    const num = Number(value);
    if (Number.isNaN(num)) return _escape(value ?? "0");
    return num.toFixed(2);
  }

  function _escape(value) {
    return String(value ?? "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  /* ---- zoom ---- */

  function zoomIn()  { scale = Math.min(scale + 0.15, 3); _applyScale(); }
  function zoomOut() { scale = Math.max(scale - 0.15, 0.3); _applyScale(); }
  function zoomReset() { scale = 1; _applyScale(); }

  function _applyScale() {
    if (!svg) return;
    const vb = svg.getAttribute("viewBox");
    if (!vb) return;
    const [,, w, h] = vb.split(" ").map(Number);
    svg.setAttribute("width",  w * scale);
    svg.setAttribute("height", h * scale);
  }

  return { init, render, renderPreview, zoomIn, zoomOut, zoomReset };
})();
