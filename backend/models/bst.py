"""
BST — Standard Binary Search Tree ordered by flight_code.
Implements ITree.  Base class for AVLTree (Liskov Substitution).
"""

from models.interfaces import ITree
from models.flight_node import FlightNode


class BST(ITree):
    """Binary Search Tree with flight_code as the ordering key."""

    def __init__(self):
        self.root = None
        self.size = 0

    # ------------------------------------------------------------------
    # ITree public API
    # ------------------------------------------------------------------

    def insert(self, node: FlightNode):
        self.root = self._insert_rec(self.root, node, None)
        self.size += 1

    def delete(self, flight_code: str) -> dict:
        target = self.search(flight_code)
        if target is None:
            raise ValueError(f"Flight {flight_code} not found")
        snapshot = target.to_dict()
        self.root = self._delete_rec(self.root, flight_code)
        self._fix_root_parent()
        self.size -= 1
        return snapshot

    def search(self, flight_code: str):
        return self._search_rec(self.root, flight_code)

    def get_root(self):
        return self.root

    def get_height(self) -> int:
        return self.root.height if self.root else 0

    def get_leaf_count(self) -> int:
        return self._count_leaves(self.root)

    def is_empty(self) -> bool:
        return self.root is None

    # ------------------------------------------------------------------
    # Recursive helpers
    # ------------------------------------------------------------------

    def _insert_rec(self, current, node, parent):
        if current is None:
            node.parent = parent
            node.height = 1
            node.balance_factor = 0
            return node

        if node.flight_code < current.flight_code:
            current.left_child = self._insert_rec(
                current.left_child, node, current
            )
        elif node.flight_code > current.flight_code:
            current.right_child = self._insert_rec(
                current.right_child, node, current
            )
        else:
            raise ValueError(
                f"Flight {node.flight_code} already exists in the tree"
            )

        self._update_height(current)
        return current

    def _delete_rec(self, current, code):
        if current is None:
            return None

        if code < current.flight_code:
            current.left_child = self._delete_rec(current.left_child, code)
            self._link_parent(current.left_child, current)
        elif code > current.flight_code:
            current.right_child = self._delete_rec(current.right_child, code)
            self._link_parent(current.right_child, current)
        else:
            # Found the node — handle 0, 1, or 2 children
            if current.left_child is None:
                return current.right_child
            if current.right_child is None:
                return current.left_child
            # Two children: replace with in-order successor
            successor = self._find_min(current.right_child)
            current.copy_data_from(successor)
            current.right_child = self._delete_rec(
                current.right_child, successor.flight_code
            )
            self._link_parent(current.right_child, current)

        self._update_height(current)
        return current

    def _search_rec(self, current, code):
        if current is None:
            return None
        if code == current.flight_code:
            return current
        if code < current.flight_code:
            return self._search_rec(current.left_child, code)
        return self._search_rec(current.right_child, code)

    # ------------------------------------------------------------------
    # Utility
    # ------------------------------------------------------------------

    def _find_min(self, node):
        while node.left_child:
            node = node.left_child
        return node

    def _update_height(self, node):
        if node is None:
            return
        lh = node.left_child.height if node.left_child else 0
        rh = node.right_child.height if node.right_child else 0
        node.height = 1 + max(lh, rh)
        node.balance_factor = lh - rh

    @staticmethod
    def _link_parent(child, parent):
        if child is not None:
            child.parent = parent

    def _fix_root_parent(self):
        if self.root:
            self.root.parent = None

    def _count_leaves(self, node) -> int:
        if node is None:
            return 0
        if node.is_leaf():
            return 1
        return self._count_leaves(node.left_child) + self._count_leaves(
            node.right_child
        )
