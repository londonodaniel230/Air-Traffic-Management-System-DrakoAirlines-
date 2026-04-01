"""
ProfitabilityAnalyzer — finds the least profitable flight based on
the formula: passengers × finalPrice − promotion + penalty.
Tiebreakers: deepest node, then highest flight_code.
"""


class ProfitabilityAnalyzer:
    """Provides profitability analysis and smart-delete target selection."""

    def __init__(self, tree):
        self.tree = tree

    def calculate(self, node) -> float:
        return node.passengers * node.final_price - node.promotion + node.penalty

    def find_least_profitable(self):
        """Return the least profitable FlightNode (or None)."""
        if self.tree.is_empty():
            return None

        candidates = []
        self._collect(self.tree.get_root(), 0, candidates)

        # 1. Minimum profitability
        min_prof = min(c[0] for c in candidates)
        finalists = [c for c in candidates if c[0] == min_prof]

        # 2. Deepest (farthest from root)
        max_depth = max(c[1] for c in finalists)
        finalists = [c for c in finalists if c[1] == max_depth]

        # 3. Highest flight_code
        finalists.sort(key=lambda c: c[2].flight_code, reverse=True)
        return finalists[0][2]

    def get_ranking(self) -> list:
        nodes = []
        self._collect(self.tree.get_root(), 0, nodes)
        nodes.sort(key=lambda c: c[0])
        return [
            {
                "flight_code": n[2].flight_code,
                "profitability": n[0],
                "depth": n[1],
            }
            for n in nodes
        ]

    # ------------------------------------------------------------------

    def _collect(self, node, depth, acc):
        if node is None:
            return
        acc.append((self.calculate(node), depth, node))
        self._collect(node.left_child, depth + 1, acc)
        self._collect(node.right_child, depth + 1, acc)
