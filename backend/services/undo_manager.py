"""
Undo system — Action hierarchy + stack-based UndoManager.
Open/Closed: new action types extend Action without touching UndoManager.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from models.flight_node import FlightNode


# ======================================================================
# Abstract action
# ======================================================================

class Action(ABC):
    """Base class for all reversible operations."""

    def __init__(self, description: str):
        self.timestamp = datetime.now()
        self.description = description

    @abstractmethod
    def undo(self):
        """Reverse this action."""

    def to_dict(self) -> dict:
        return {
            "type": self.__class__.__name__,
            "description": self.description,
            "timestamp": self.timestamp.isoformat(),
        }


# ======================================================================
# Concrete actions
# ======================================================================

class InsertAction(Action):
    """Reversal: delete the inserted node."""

    def __init__(self, node_data: dict, tree):
        super().__init__(f"Insert {node_data['flight_code']}")
        self.node_data = node_data
        self.tree = tree

    def undo(self):
        self.tree.delete(self.node_data["flight_code"])


class DeleteAction(Action):
    """Reversal: re-insert the deleted node."""

    def __init__(self, node_data: dict, tree):
        super().__init__(f"Delete {node_data['flight_code']}")
        self.node_data = node_data
        self.tree = tree

    def undo(self):
        node = FlightNode.from_dict(self.node_data)
        self.tree.insert(node)


class ModifyAction(Action):
    """Reversal: restore old data on the node."""

    def __init__(self, flight_code: str, old_data: dict, tree):
        super().__init__(f"Modify {flight_code}")
        self.flight_code = flight_code
        self.old_data = old_data
        self.tree = tree

    def undo(self):
        node = self.tree.search(self.flight_code)
        if node is None:
            return
        for key in ("origin", "destination", "base_price", "passengers",
                     "promotion", "priority", "alerts"):
            if key in self.old_data:
                setattr(node, key, self.old_data[key])
        node.update_final_price()


class CancelAction(Action):
    """Reversal: re-insert every node from the cancelled sub-tree."""

    def __init__(self, subtree_data: list, tree):
        code = subtree_data[0]["flight_code"] if subtree_data else "?"
        super().__init__(f"Cancel {code} ({len(subtree_data)} nodes)")
        self.subtree_data = subtree_data
        self.tree = tree

    def undo(self):
        for nd in self.subtree_data:
            try:
                self.tree.insert(FlightNode.from_dict(nd))
            except ValueError:
                pass  # duplicate — already present


# ======================================================================
# Undo manager (stack)
# ======================================================================

class UndoManager:
    """LIFO stack of Action objects with optional max depth."""

    def __init__(self, max_size: int = 200):
        self._stack: list[Action] = []
        self.max_size = max_size

    def push(self, action: Action):
        if len(self._stack) >= self.max_size:
            self._stack.pop(0)
        self._stack.append(action)

    def undo(self) -> Action:
        if not self.can_undo():
            raise ValueError("Nothing to undo")
        action = self._stack.pop()
        action.undo()
        return action

    def peek(self):
        return self._stack[-1] if self._stack else None

    def can_undo(self) -> bool:
        return len(self._stack) > 0

    def get_history(self) -> list:
        return [a.to_dict() for a in reversed(self._stack)]

    def clear(self):
        self._stack.clear()
