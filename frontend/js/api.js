/* ==================================================================
   api.js — thin HTTP client that talks to the Flask REST API.
   Every method returns a Promise<Object>.
   ================================================================== */

const API = (() => {
  const BASE = "/api";

  async function _json(url, opts = {}) {
    const res = await fetch(BASE + url, {
      headers: { "Content-Type": "application/json" },
      ...opts,
    });
    const body = await res.json();
    if (!res.ok) throw new Error(body.error || res.statusText);
    return body;
  }

  return {
    /* ---- tree state ---- */
    getTree:        ()           => _json("/tree"),

    /* ---- load / export ---- */
    loadJSON:       (data)       => _json("/load",  { method: "POST", body: JSON.stringify(data) }),
    exportTree:     ()           => _json("/export"),

    /* ---- flight CRUD ---- */
    createFlight:   (data)       => _json("/flight", { method: "POST", body: JSON.stringify(data) }),
    modifyFlight:   (code, data) => _json(`/flight/${code}`, { method: "PUT",  body: JSON.stringify(data) }),
    deleteFlight:   (code)       => _json(`/flight/${code}`, { method: "DELETE" }),
    cancelFlight:   (code)       => _json(`/flight/${code}/cancel`, { method: "POST" }),

    /* ---- undo ---- */
    undo:           ()           => _json("/undo", { method: "POST" }),
    undoHistory:    ()           => _json("/undo/history"),

    /* ---- smart delete ---- */
    smartDelete:    ()           => _json("/smart-delete", { method: "POST" }),

    /* ---- versions ---- */
    saveVersion:    (name)       => _json("/version",  { method: "POST", body: JSON.stringify({ name }) }),
    listVersions:   ()           => _json("/versions"),
    restoreVersion: (name)       => _json(`/version/${name}/restore`, { method: "POST" }),

    /* ---- queue ---- */
    queueAdd:       (data)       => _json("/queue/add", { method: "POST", body: JSON.stringify(data) }),
    queueNext:      ()           => _json("/queue/process-next", { method: "POST" }),
    queueAll:       ()           => _json("/queue/process-all",  { method: "POST" }),
    queueStatus:    ()           => _json("/queue/status"),

    /* ---- stress ---- */
    toggleStress:   ()           => _json("/stress/toggle",   { method: "POST" }),
    rebalance:      ()           => _json("/stress/rebalance", { method: "POST" }),

    /* ---- audit ---- */
    audit:          ()           => _json("/audit", { method: "POST" }),

    /* ---- metrics / traversals ---- */
    getMetrics:     ()           => _json("/metrics"),
    getTraversals:  ()           => _json("/traversals"),

    /* ---- penalty ---- */
    setDepth:       (depth)      => _json("/penalty/depth", { method: "PUT", body: JSON.stringify({ depth }) }),

    /* ---- profitability ---- */
    getProfitability: ()         => _json("/profitability"),
  };
})();
