"""
TreeSerializer — JSON serialization / deserialization of tree structures.
Handles topology mode (rebuild from hierarchy) and insertion mode (one-by-one).
"""

import json
from models.flight_node import FlightNode
from models.avl_tree import AVLTree
from models.bst import BST


class TreeSerializer:
    """Serializes/deserializes AVL and BST trees to/from dicts (JSON-ready)."""

    # ------------------------------------------------------------------
    # Serialize
    # ------------------------------------------------------------------

    def serialize_tree(self, tree) -> dict:
        """Full hierarchical serialization of a tree."""
        return {
            "load_mode": "topology",
            "root": self._ser_node(tree.get_root()),
            "size": tree.size,
            "height": tree.get_height(),
            "stress_mode": getattr(tree, "stress_mode", False),
            "rotation_stats": (
                tree.rotation_stats.get_summary()
                if hasattr(tree, "rotation_stats")
                else {}
            ),
        }

    def _ser_node(self, node) -> dict | None:
        if node is None:
            return None
        data = node.to_dict()
        data["left"] = self._ser_node(node.left_child)
        data["right"] = self._ser_node(node.right_child)
        return data

    # ------------------------------------------------------------------
    # Deserialize — topology
    # ------------------------------------------------------------------

    def deserialize_topology(self, data: dict) -> AVLTree:
        """Rebuild an AVL respecting the topology described in *data*."""
        tree = AVLTree()
        root_data = data.get("root")
        if root_data:
            tree.root = self._build_topo(root_data, None)
            tree.size = self._count(tree.root)
        return tree

    def _build_topo(self, nd, parent):
        if nd is None:
            return None
        node = FlightNode.from_dict(nd)
        node.parent = parent
        node.left_child = self._build_topo(nd.get("left"), node)
        node.right_child = self._build_topo(nd.get("right"), node)
        # Recalculate height / BF
        lh = node.left_child.height if node.left_child else 0
        rh = node.right_child.height if node.right_child else 0
        node.height = 1 + max(lh, rh)
        node.balance_factor = lh - rh
        return node

    # ------------------------------------------------------------------
    # Deserialize — insertion
    # ------------------------------------------------------------------

    def deserialize_insertion(self, data: dict):
        """Insert flights one-by-one into an AVL and a BST. Returns (avl, bst)."""
        avl = AVLTree()
        bst = BST()
        for fd in data.get("flights", []):
            avl.insert(FlightNode.from_dict(fd))
            bst.insert(FlightNode.from_dict(fd))
        return avl, bst

    # ------------------------------------------------------------------
    # Export
    # ------------------------------------------------------------------

    def export_to_json(self, tree, filepath: str):
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(self.serialize_tree(tree), f, indent=2, ensure_ascii=False)

    # ------------------------------------------------------------------

    def _count(self, node) -> int:
        if node is None:
            return 0
        return 1 + self._count(node.left_child) + self._count(node.right_child)
