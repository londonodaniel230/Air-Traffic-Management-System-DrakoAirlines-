"""
AVLTree — Self-balancing AVL tree extending BST.
Adds rotations, stress mode, flight cancellation (subtree removal),
and global rebalance.  Open/Closed: extends BST without modifying it.
"""

from models.bst import BST
from models.flight_node import FlightNode
from models.rotation_stats import RotationStats


class AVLTree(BST):
    """AVL tree with automatic balancing, stress mode and subtree cancellation."""

    def __init__(self):
        super().__init__()
        self.stress_mode = False
        self.rotation_stats = RotationStats()

    # ------------------------------------------------------------------
    # Insert (override)
    # ------------------------------------------------------------------

    def insert(self, node: FlightNode):
        self.root = self._avl_insert(self.root, node, None)
        self.size += 1

    def _avl_insert(self, current, node, parent):
        if current is None:
            node.parent = parent
            node.height = 1
            node.balance_factor = 0
            return node

        if node.flight_code < current.flight_code:
            current.left_child = self._avl_insert(
                current.left_child, node, current
            )
        elif node.flight_code > current.flight_code:
            current.right_child = self._avl_insert(
                current.right_child, node, current
            )
        else:
            raise ValueError(
                f"Flight {node.flight_code} already exists in the tree"
            )

        self._update_height(current)
        if not self.stress_mode:
            current = self._balance(current)
        return current

    # ------------------------------------------------------------------
    # Delete single node (override)
    # ------------------------------------------------------------------

    def delete(self, flight_code: str) -> dict:
        target = self.search(flight_code)
        if target is None:
            raise ValueError(f"Flight {flight_code} not found")
        snapshot = target.to_dict()
        self.root = self._avl_delete(self.root, flight_code)
        self._fix_root_parent()
        self.size -= 1
        return snapshot

    def _avl_delete(self, current, code):
        if current is None:
            return None

        if code < current.flight_code:
            current.left_child = self._avl_delete(current.left_child, code)
            self._link_parent(current.left_child, current)
        elif code > current.flight_code:
            current.right_child = self._avl_delete(current.right_child, code)
            self._link_parent(current.right_child, current)
        else:
            if current.left_child is None:
                return current.right_child
            if current.right_child is None:
                return current.left_child
            successor = self._find_min(current.right_child)
            current.copy_data_from(successor)
            current.right_child = self._avl_delete(
                current.right_child, successor.flight_code
            )
            self._link_parent(current.right_child, current)

        self._update_height(current)
        if not self.stress_mode:
            current = self._balance(current)
        return current

    # ------------------------------------------------------------------
    # Cancel flight (delete entire sub-tree)
    # ------------------------------------------------------------------

    def cancel_flight(self, flight_code: str) -> list:
        """Remove node + all descendants. Returns list[dict] for undo."""
        node = self.search(flight_code)
        if node is None:
            raise ValueError(f"Flight {flight_code} not found")

        subtree_data = self._collect_subtree(node)
        parent = node.parent

        # Disconnect from parent
        if parent is None:
            self.root = None
        elif parent.left_child is node:
            parent.left_child = None
        else:
            parent.right_child = None
        node.parent = None

        self.size -= len(subtree_data)
        self.rotation_stats.increment_cancellation()

        # Rebalance upward from parent
        if not self.stress_mode and parent is not None:
            self._rebalance_upward(parent)

        return subtree_data

    def _collect_subtree(self, node) -> list:
        """Pre-order collection of all nodes in a sub-tree as dicts."""
        if node is None:
            return []
        result = [node.to_dict()]
        result.extend(self._collect_subtree(node.left_child))
        result.extend(self._collect_subtree(node.right_child))
        return result

    def _rebalance_upward(self, node):
        """Walk from *node* to the root, balancing at each level."""
        current = node
        while current is not None:
            self._update_height(current)
            parent = current.parent
            balanced = self._balance(current)

            if parent is None:
                self.root = balanced
                balanced.parent = None
            elif parent.left_child is current:
                parent.left_child = balanced
                balanced.parent = parent
            else:
                parent.right_child = balanced
                balanced.parent = parent

            current = parent

    # ------------------------------------------------------------------
    # Rotations
    # ------------------------------------------------------------------

    def _balance(self, node):
        """Apply rotation if |BF| > 1. Returns new sub-tree root."""
        if node is None:
            return None

        bf = self._bf(node)

        # Left-heavy
        if bf > 1:
            if self._bf(node.left_child) < 0:
                # Left-Right case
                node.left_child = self._rotate_left(node.left_child)
                self._link_parent(node.left_child, node)
                result = self._rotate_right(node)
                self.rotation_stats.increment("left_right")
            else:
                # Left-Left case → single right rotation
                result = self._rotate_right(node)
                self.rotation_stats.increment("right")
            self._propagate_parents(result)
            return result

        # Right-heavy
        if bf < -1:
            if self._bf(node.right_child) > 0:
                # Right-Left case
                node.right_child = self._rotate_right(node.right_child)
                self._link_parent(node.right_child, node)
                result = self._rotate_left(node)
                self.rotation_stats.increment("right_left")
            else:
                # Right-Right case → single left rotation
                result = self._rotate_left(node)
                self.rotation_stats.increment("left")
            self._propagate_parents(result)
            return result

        return node

    def _rotate_left(self, z):
        y = z.right_child
        t2 = y.left_child

        y.left_child = z
        z.right_child = t2

        if t2:
            t2.parent = z
        y.parent = z.parent
        z.parent = y

        self._update_height(z)
        self._update_height(y)
        return y

    def _rotate_right(self, z):
        y = z.left_child
        t3 = y.right_child

        y.right_child = z
        z.left_child = t3

        if t3:
            t3.parent = z
        y.parent = z.parent
        z.parent = y

        self._update_height(z)
        self._update_height(y)
        return y

    @staticmethod
    def _propagate_parents(node):
        """Ensure immediate children have correct parent pointer."""
        if node is None:
            return
        if node.left_child:
            node.left_child.parent = node
        if node.right_child:
            node.right_child.parent = node

    def _bf(self, node) -> int:
        if node is None:
            return 0
        lh = node.left_child.height if node.left_child else 0
        rh = node.right_child.height if node.right_child else 0
        return lh - rh

    # ------------------------------------------------------------------
    # Stress mode & Global rebalance
    # ------------------------------------------------------------------

    def toggle_stress_mode(self) -> bool:
        self.stress_mode = not self.stress_mode
        return self.stress_mode

    def global_rebalance(self) -> dict:
        """Rebalance entire tree bottom-up. Returns report dict."""
        initial_height = self.get_height()
        snap = self.rotation_stats.get_summary()

        self.stress_mode = False
        self.root = self._rebalance_subtree(self.root)
        self._fix_root_parent()

        after = self.rotation_stats.get_summary()
        return {
            "initial_height": initial_height,
            "final_height": self.get_height(),
            "rotations": {
                k: after[k] - snap[k]
                for k in ("left", "right", "left_right", "right_left")
            },
            "total_new_rotations": after["total_rotations"] - snap["total_rotations"],
        }

    def _rebalance_subtree(self, node):
        """Post-order recursive rebalance of an entire sub-tree."""
        if node is None:
            return None

        node.left_child = self._rebalance_subtree(node.left_child)
        self._link_parent(node.left_child, node)

        node.right_child = self._rebalance_subtree(node.right_child)
        self._link_parent(node.right_child, node)

        self._update_height(node)
        return self._balance(node)
