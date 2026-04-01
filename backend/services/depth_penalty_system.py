"""
DepthPenaltySystem — applies a 25 % price increase to nodes that exceed
a user-defined critical depth.
"""


class DepthPenaltySystem:
    """Evaluates node depth vs threshold and adjusts final prices."""

    PENALTY_RATE = 0.25  # 25 %

    def __init__(self, tree, critical_depth: int = 5):
        self.tree = tree
        self.critical_depth = critical_depth

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------

    def set_critical_depth(self, depth: int):
        self.critical_depth = depth
        self.recalculate_all_prices()

    def get_critical_depth(self) -> int:
        return self.critical_depth

    def recalculate_all_prices(self):
        """Re-evaluate every node against the current depth threshold."""
        self._recalc(self.tree.get_root(), 0)

    def evaluate_all_nodes(self) -> list:
        """Return a list of all currently critical nodes."""
        critical = []
        self._evaluate(self.tree.get_root(), 0, critical)
        return critical

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _recalc(self, node, depth):
        if node is None:
            return
        if depth >= self.critical_depth:
            node.is_critical = True
            node.penalty = node.base_price * self.PENALTY_RATE
        else:
            node.is_critical = False
            node.penalty = 0.0
        node.update_final_price()
        self._recalc(node.left_child, depth + 1)
        self._recalc(node.right_child, depth + 1)

    def _evaluate(self, node, depth, acc):
        if node is None:
            return
        if depth >= self.critical_depth:
            acc.append(node)
        self._evaluate(node.left_child, depth + 1, acc)
        self._evaluate(node.right_child, depth + 1, acc)

    def get_node_depth(self, node) -> int:
        depth = 0
        cur = node
        while cur.parent:
            depth += 1
            cur = cur.parent
        return depth
