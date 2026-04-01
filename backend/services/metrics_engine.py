"""
MetricsEngine — real-time analytical metrics for the AVL dashboard.
"""


class MetricsEngine:
    """Aggregates tree statistics for the front-end dashboard."""

    def __init__(self, tree, traversal_service):
        self.tree = tree
        self.traversal = traversal_service

    def get_height(self) -> int:
        return self.tree.get_height()

    def get_rotation_stats(self) -> dict:
        return self.tree.rotation_stats.get_summary()

    def get_leaf_count(self) -> int:
        return self.tree.get_leaf_count()

    def get_node_count(self) -> int:
        return self.tree.size

    def get_all_traversals(self) -> dict:
        return {
            "bfs": [n.to_dict() for n in self.traversal.breadth_first()],
            "pre_order": [n.to_dict() for n in self.traversal.pre_order()],
            "in_order": [n.to_dict() for n in self.traversal.in_order()],
            "post_order": [n.to_dict() for n in self.traversal.post_order()],
        }

    def get_dashboard_data(self) -> dict:
        return {
            "height": self.get_height(),
            "node_count": self.get_node_count(),
            "leaf_count": self.get_leaf_count(),
            "rotation_stats": self.get_rotation_stats(),
            "is_empty": self.tree.is_empty(),
            "stress_mode": getattr(self.tree, "stress_mode", False),
        }
