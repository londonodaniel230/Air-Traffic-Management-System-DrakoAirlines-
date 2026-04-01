"""
FlightManager — façade that orchestrates CRUD operations on the AVL tree
and records every action in the UndoManager.
"""

from models.flight_node import FlightNode
from services.undo_manager import (
    UndoManager, InsertAction, DeleteAction, ModifyAction, CancelAction,
)


class FlightManager:
    """High-level CRUD + undo for flights."""

    def __init__(self, avl_tree, penalty_system):
        self.avl_tree = avl_tree
        self.penalty_system = penalty_system
        self.undo_manager = UndoManager()

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    def create_flight(self, data: dict) -> FlightNode:
        node = FlightNode.from_dict(data) if isinstance(data, dict) else data
        self.avl_tree.insert(node)
        self.penalty_system.recalculate_all_prices()
        self.undo_manager.push(InsertAction(node.to_dict(), self.avl_tree))
        return node

    def modify_flight(self, code: str, data: dict) -> FlightNode:
        node = self.avl_tree.search(code)
        if node is None:
            raise ValueError(f"Flight {code} not found")
        old_data = node.to_dict()

        for key in ("origin", "destination", "base_price",
                     "passengers", "promotion", "priority", "alerts"):
            if key in data:
                setattr(node, key,
                        float(data[key]) if key == "base_price"
                        else int(data[key]) if key in ("passengers", "priority")
                        else float(data[key]) if key == "promotion"
                        else data[key])
        node.update_final_price()
        self.penalty_system.recalculate_all_prices()

        self.undo_manager.push(ModifyAction(code, old_data, self.avl_tree))
        return node

    def delete_flight(self, code: str) -> dict:
        snapshot = self.avl_tree.delete(code)
        self.penalty_system.recalculate_all_prices()
        self.undo_manager.push(DeleteAction(snapshot, self.avl_tree))
        return snapshot

    def cancel_flight(self, code: str) -> list:
        subtree = self.avl_tree.cancel_flight(code)
        self.penalty_system.recalculate_all_prices()
        self.undo_manager.push(CancelAction(subtree, self.avl_tree))
        return subtree

    # ------------------------------------------------------------------
    # Undo
    # ------------------------------------------------------------------

    def undo(self) -> dict:
        action = self.undo_manager.undo()
        self.penalty_system.recalculate_all_prices()
        return action.to_dict()

    def can_undo(self) -> bool:
        return self.undo_manager.can_undo()

    def get_undo_history(self) -> list:
        return self.undo_manager.get_history()
