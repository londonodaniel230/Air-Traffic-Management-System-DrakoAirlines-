/* ==================================================================
   metrics_dashboard.js — updates the right-panel metric cells
   and traversal output.
   ================================================================== */

const MetricsDashboard = (() => {

  function update(metrics) {
    if (!metrics) return;
    _set("m-height",    metrics.height);
    _set("m-nodes",     metrics.node_count);
    _set("m-leaves",    metrics.leaf_count);

    const r = metrics.rotation_stats || {};
    _set("m-rot-l",     r.left            ?? 0);
    _set("m-rot-r",     r.right           ?? 0);
    _set("m-rot-lr",    r.left_right      ?? 0);
    _set("m-rot-rl",    r.right_left      ?? 0);
    _set("m-rot-total", r.total_rotations ?? 0);
    _set("m-cancel",    r.total_cancellations ?? 0);
  }

  function showTraversal(name, data) {
    const box = document.getElementById("traversal-output");
    if (!box) return;
    const list = data[name] || [];
    if (list.length === 0) {
      box.textContent = "(vacío)";
      return;
    }
    box.textContent = list.map(n =>
      `${n.flight_code}  [${n.origin}→${n.destination}]  $${n.final_price}` +
      (n.is_critical ? "  ⚠ CRÍTICO" : "")
    ).join("\n");
  }

  function _set(id, val) {
    const el = document.getElementById(id);
    if (el) el.textContent = val;
  }

  return { update, showTraversal };
})();
