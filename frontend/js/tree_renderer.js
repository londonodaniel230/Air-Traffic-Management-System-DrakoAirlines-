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
  let svg, container;

  function init() {
    svg       = document.getElementById("tree-svg");
    container = document.getElementById("tree-container");
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

  function render(treeData) {
    if (!svg) init();

    const root = treeData && treeData.root ? treeData.root : null;
    const emptyMsg = document.getElementById("tree-empty-msg");

    if (!root) {
      svg.innerHTML = "";
      if (emptyMsg) emptyMsg.style.display = "";
      return;
    }
    if (emptyMsg) emptyMsg.style.display = "none";

    const pos   = _positions(root);
    const codes = Object.keys(pos);
    const maxX  = Math.max(...codes.map(c => pos[c].x)) + PAD + NODE_R;
    const maxY  = Math.max(...codes.map(c => pos[c].y)) + PAD + NODE_R + 30;

    svg.setAttribute("width",  maxX * scale);
    svg.setAttribute("height", maxY * scale);
    svg.setAttribute("viewBox", `0 0 ${maxX} ${maxY}`);

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
      const cls = data.is_critical ? "tree-node critical" : "tree-node";
      html += `<g class="${cls}" data-code="${code}">`;
      html += `<circle cx="${x}" cy="${y}" r="${NODE_R}"/>`;
      html += `<text x="${x}" y="${y - 4}">${code}</text>`;
      html += `<text class="node-bf" x="${x}" y="${y + 12}">BF ${data.balance_factor ?? "?"}</text>`;
      html += `</g>`;
    }

    svg.innerHTML = html;
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

  return { init, render, zoomIn, zoomOut, zoomReset };
})();
