"""
AVLTree - Self-balancing AVL tree extending BST.
Adds rotations, stress mode, flight cancellation (subtree removal),
global rebalance, and structural tracing for visual playback.
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
        self.last_operation_trace = None
        self._trace_sequence = 0
        self._trace_runtime = None
        self._pending_trace_events = []

    # ------------------------------------------------------------------
    # Insert (override)
    # ------------------------------------------------------------------

    def insert(self, node: FlightNode):
        self._start_operation_trace("insert", node.flight_code)
        try:
            self.root, inserted = self._avl_insert(self.root, node, None)
            self.size += 1
            self._fix_root_parent()
            self._flush_pending_trace_events()

            if inserted and not self._trace_runtime["insert_recorded"]:
                self._record_trace_step(
                    "Nodo insertado",
                    f"{node.flight_code} quedó como nueva raíz del árbol.",
                    [node.flight_code],
                )

            self._record_trace_step(
                "Resultado final",
                f"Árbol balanceado tras insertar {node.flight_code}.",
                [node.flight_code],
            )
            self._finish_operation_trace()
        except Exception:
            self._discard_operation_trace()
            raise

    def _avl_insert(self, current, node, parent):
        if current is None:
            node.parent = parent
            node.height = 1
            node.balance_factor = 0
            return node, True

        if node.flight_code < current.flight_code:
            current.left_child, inserted = self._avl_insert(
                current.left_child, node, current
            )
            self._link_parent(current.left_child, current)
            self._flush_pending_trace_events()
            if inserted and not self._trace_runtime["insert_recorded"]:
                self._trace_runtime["insert_recorded"] = True
                self._record_trace_step(
                    "Nodo insertado",
                    f"{node.flight_code} se insertó a la izquierda de {current.flight_code}.",
                    [node.flight_code, current.flight_code],
                )
        elif node.flight_code > current.flight_code:
            current.right_child, inserted = self._avl_insert(
                current.right_child, node, current
            )
            self._link_parent(current.right_child, current)
            self._flush_pending_trace_events()
            if inserted and not self._trace_runtime["insert_recorded"]:
                self._trace_runtime["insert_recorded"] = True
                self._record_trace_step(
                    "Nodo insertado",
                    f"{node.flight_code} se insertó a la derecha de {current.flight_code}.",
                    [node.flight_code, current.flight_code],
                )
        else:
            raise ValueError(
                f"Flight {node.flight_code} already exists in the tree"
            )

        self._update_height(current)
        if not self.stress_mode:
            current = self._balance(current)
        return current, inserted

    # ------------------------------------------------------------------
    # Delete single node (override)
    # ------------------------------------------------------------------

    def delete(self, flight_code: str) -> dict:
        target = self.search(flight_code)
        if target is None:
            raise ValueError(f"Flight {flight_code} not found")
        snapshot = target.to_dict()

        self._start_operation_trace("delete", flight_code)
        try:
            self.root, deleted = self._avl_delete(self.root, flight_code)
            self._fix_root_parent()
            self.size -= 1
            self._flush_pending_trace_events()

            if deleted and self._trace_runtime["deleted_code"] is None:
                self._record_trace_step(
                    "Nodo eliminado",
                    f"Se eliminó el nodo {flight_code}.",
                    [flight_code],
                )

            self._record_trace_step(
                "Resultado final",
                f"Árbol balanceado tras eliminar {flight_code}.",
                [flight_code],
            )
            self._finish_operation_trace()
        except Exception:
            self._discard_operation_trace()
            raise

        return snapshot

    def _avl_delete(self, current, code):
        if current is None:
            return None, False

        if code < current.flight_code:
            current.left_child, deleted = self._avl_delete(current.left_child, code)
            self._link_parent(current.left_child, current)
            self._flush_pending_trace_events()
        elif code > current.flight_code:
            current.right_child, deleted = self._avl_delete(current.right_child, code)
            self._link_parent(current.right_child, current)
            self._flush_pending_trace_events()
        else:
            if current.left_child is None:
                self._queue_delete_event(current.flight_code, current.right_child)
                return current.right_child, True
            if current.right_child is None:
                self._queue_delete_event(current.flight_code, current.left_child)
                return current.left_child, True

            removed_code = current.flight_code
            successor = self._find_min(current.right_child)
            successor_code = successor.flight_code
            current.copy_data_from(successor)
            self._record_trace_step(
                "Reemplazo por sucesor",
                f"{removed_code} fue reemplazado por su sucesor in-order {successor_code}.",
                [current.flight_code],
            )
            current.right_child, deleted = self._avl_delete(
                current.right_child, successor.flight_code
            )
            self._link_parent(current.right_child, current)
            self._flush_pending_trace_events()

        self._update_height(current)
        if not self.stress_mode:
            current = self._balance(current)
        return current, deleted

    # ------------------------------------------------------------------
    # Cancel flight (delete entire sub-tree)
    # ------------------------------------------------------------------

    def cancel_flight(self, flight_code: str) -> list:
        """Remove node + all descendants. Returns list[dict] for undo."""
        node = self.search(flight_code)
        if node is None:
            raise ValueError(f"Flight {flight_code} not found")

        self.clear_last_operation_trace()
        subtree_data = self._collect_subtree(node)
        parent = node.parent

        if parent is None:
            self.root = None
        elif parent.left_child is node:
            parent.left_child = None
        else:
            parent.right_child = None
        node.parent = None

        self.size -= len(subtree_data)
        self.rotation_stats.increment_cancellation()

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

        if bf > 1:
            if self._bf(node.left_child) < 0:
                node.left_child = self._rotate_left(node.left_child)
                self._link_parent(node.left_child, node)
                result = self._rotate_right(node)
                self.rotation_stats.increment("left_right")
                self._queue_trace_event(
                    "Rotación izquierda-derecha",
                    f"Se rebalanceó el subárbol con raíz en {node.flight_code} usando una rotación izquierda-derecha.",
                    [result.flight_code, node.flight_code],
                )
            else:
                result = self._rotate_right(node)
                self.rotation_stats.increment("right")
                self._queue_trace_event(
                    "Rotación simple a la derecha",
                    f"Se rebalanceó el subárbol con raíz en {node.flight_code} con una rotación a la derecha.",
                    [result.flight_code, node.flight_code],
                )
            self._propagate_parents(result)
            return result

        if bf < -1:
            if self._bf(node.right_child) > 0:
                node.right_child = self._rotate_right(node.right_child)
                self._link_parent(node.right_child, node)
                result = self._rotate_left(node)
                self.rotation_stats.increment("right_left")
                self._queue_trace_event(
                    "Rotación derecha-izquierda",
                    f"Se rebalanceó el subárbol con raíz en {node.flight_code} usando una rotación derecha-izquierda.",
                    [result.flight_code, node.flight_code],
                )
            else:
                result = self._rotate_left(node)
                self.rotation_stats.increment("left")
                self._queue_trace_event(
                    "Rotación simple a la izquierda",
                    f"Se rebalanceó el subárbol con raíz en {node.flight_code} con una rotación a la izquierda.",
                    [result.flight_code, node.flight_code],
                )
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
        return_value = not self.stress_mode
        self.stress_mode = return_value
        return return_value

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

    # ------------------------------------------------------------------
    # Trace helpers
    # ------------------------------------------------------------------

    def get_last_operation_trace(self) -> dict | None:
        return self.last_operation_trace

    def clear_last_operation_trace(self):
        self.last_operation_trace = None

    def _start_operation_trace(self, action: str, target: str):
        self._trace_runtime = {
            "action": action,
            "target": target,
            "steps": [],
            "insert_recorded": False,
            "deleted_code": None,
        }
        self._pending_trace_events = []
        self._record_trace_step(
            "Estado inicial",
            f"Estado del árbol antes de {self._action_label(action)} {target}.",
            [target],
        )

    def _finish_operation_trace(self):
        if self._trace_runtime is None:
            return

        self._trace_sequence += 1
        self.last_operation_trace = {
            "id": self._trace_sequence,
            "action": self._trace_runtime["action"],
            "target": self._trace_runtime["target"],
            "steps": list(self._trace_runtime["steps"]),
        }
        self._trace_runtime = None
        self._pending_trace_events = []

    def _discard_operation_trace(self):
        self._trace_runtime = None
        self._pending_trace_events = []

    def _queue_trace_event(self, title: str, detail: str, highlight_codes=None):
        if self._trace_runtime is None:
            return
        self._pending_trace_events.append({
            "title": title,
            "detail": detail,
            "highlight_codes": list(highlight_codes or []),
        })

    def _flush_pending_trace_events(self):
        while self._pending_trace_events:
            event = self._pending_trace_events.pop(0)
            self._record_trace_step(
                event["title"],
                event["detail"],
                event["highlight_codes"],
            )

    def _record_trace_step(self, title: str, detail: str, highlight_codes=None):
        if self._trace_runtime is None:
            return
        self._trace_runtime["steps"].append({
            "title": title,
            "detail": detail,
            "highlight_codes": list(highlight_codes or []),
            "tree": self._snapshot_tree(),
        })

    def _queue_delete_event(self, removed_code: str, replacement):
        replacement_code = replacement.flight_code if replacement else None
        if replacement_code:
            detail = (
                f"Se eliminó {removed_code} y su posición fue ocupada por {replacement_code}."
            )
            highlights = [removed_code, replacement_code]
        else:
            detail = f"Se eliminó {removed_code} y ese enlace quedó vacío."
            highlights = [removed_code]

        if self._trace_runtime is not None:
            self._trace_runtime["deleted_code"] = removed_code
        self._queue_trace_event("Nodo eliminado", detail, highlights)

    def _snapshot_tree(self) -> dict:
        root = self.get_root()
        return {
            "load_mode": "topology",
            "root": self._snapshot_node(root),
            "size": self._count_snapshot_nodes(root),
            "height": root.height if root else 0,
            "stress_mode": self.stress_mode,
            "rotation_stats": self.rotation_stats.get_summary(),
        }

    def _snapshot_node(self, node) -> dict | None:
        if node is None:
            return None
        data = node.to_dict()
        data["left"] = self._snapshot_node(node.left_child)
        data["right"] = self._snapshot_node(node.right_child)
        return data

    def _count_snapshot_nodes(self, node) -> int:
        if node is None:
            return 0
        return (
            1
            + self._count_snapshot_nodes(node.left_child)
            + self._count_snapshot_nodes(node.right_child)
        )

    @staticmethod
    def _action_label(action: str) -> str:
        return {
            "insert": "insertar",
            "delete": "eliminar",
        }.get(action, "actualizar")
