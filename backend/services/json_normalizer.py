"""
JSONNormalizer — translates Spanish-format flight JSON
(codigo, izquierdo, derecho …) into the internal English format
expected by TreeSerializer and FlightNode.

Auto-detects topology vs insertion mode.
"""


class JSONNormalizer:
    """Converts Spanish-keyed JSON to the internal English schema."""

    # Spanish → English field mapping
    FIELD_MAP = {
        "codigo":           "flight_code",
        "origen":           "origin",
        "destino":          "destination",
        "horaSalida":       "departure_time",
        "precioBase":       "base_price",
        "precioFinal":      "final_price",
        "pasajeros":        "passengers",
        "promocion":        "promotion",
        "alerta":           "alerts",
        "prioridad":        "priority",
        "altura":           "height",
        "factorEquilibrio": "balance_factor",
        "izquierdo":        "left",
        "derecho":          "right",
    }

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------

    def normalize(self, data: dict) -> dict:
        """Auto-detect format and return an English-schema dict."""
        if self._is_spanish_topology(data):
            return self._normalize_topology(data)
        if self._is_spanish_insertion(data):
            return self._normalize_insertion(data)
        # Already English (or unknown) — pass through
        return data

    # ------------------------------------------------------------------
    # Detection
    # ------------------------------------------------------------------

    @staticmethod
    def _is_spanish_topology(data: dict) -> bool:
        return "codigo" in data and ("izquierdo" in data or "derecho" in data)

    @staticmethod
    def _is_spanish_insertion(data: dict) -> bool:
        return (
            data.get("tipo", "").upper() == "INSERCION"
            or "vuelos" in data
        )

    # ------------------------------------------------------------------
    # Topology
    # ------------------------------------------------------------------

    def _normalize_topology(self, data: dict) -> dict:
        return {
            "load_mode": "topology",
            "root": self._normalize_node(data),
        }

    def _normalize_node(self, node) -> dict | None:
        if node is None:
            return None

        out = {}
        for es_key, en_key in self.FIELD_MAP.items():
            if es_key not in node:
                continue
            val = node[es_key]

            if es_key == "codigo":
                val = str(val)
            elif es_key == "promocion":
                val = self._coerce_promotion(val)
            elif es_key == "alerta":
                val = self._coerce_alerts(val)
            elif es_key in ("izquierdo", "derecho"):
                val = self._normalize_node(val)

            out[en_key] = val

        # Ensure required fields have defaults
        out.setdefault("priority", 1)
        out.setdefault("departure_time", "")
        return out

    # ------------------------------------------------------------------
    # Insertion
    # ------------------------------------------------------------------

    def _normalize_insertion(self, data: dict) -> dict:
        vuelos = data.get("vuelos", data.get("flights", []))
        return {
            "load_mode": "insertion",
            "flights": [self._normalize_flight(f) for f in vuelos],
        }

    def _normalize_flight(self, f: dict) -> dict:
        out = {}
        for es_key, en_key in self.FIELD_MAP.items():
            if es_key in f:
                val = f[es_key]
                if es_key == "codigo":
                    val = str(val)
                elif es_key == "promocion":
                    val = self._coerce_promotion(val)
                elif es_key == "alerta":
                    val = self._coerce_alerts(val)
                out[en_key] = val

        # Also copy any already-English keys that aren't in the map values
        for k, v in f.items():
            en = self.FIELD_MAP.get(k)
            if en is None and k not in out:
                out[k] = v

        out.setdefault("priority", f.get("prioridad", 1))
        out.setdefault("departure_time", f.get("horaSalida", ""))
        out.setdefault("alerts", [])
        out.setdefault("promotion", 0.0)
        return out

    # ------------------------------------------------------------------
    # Value coercions
    # ------------------------------------------------------------------

    @staticmethod
    def _coerce_promotion(val):
        """boolean → 0.0, number → float."""
        if isinstance(val, bool):
            return 0.0
        if isinstance(val, (int, float)):
            return float(val)
        return 0.0

    @staticmethod
    def _coerce_alerts(val):
        """boolean → list, list → list."""
        if isinstance(val, bool):
            return ["alerta activa"] if val else []
        if isinstance(val, list):
            return val
        return []
