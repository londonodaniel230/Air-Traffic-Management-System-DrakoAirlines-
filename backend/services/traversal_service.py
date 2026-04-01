"""
TraversalService — isolated traversal operations over any ITree.
Implements ITraversable.  Depends on abstraction (ITree), not concrete class.
"""

from collections import deque
from models.interfaces import ITraversable


class TraversalService(ITraversable):
    """Provides BFS and DFS traversals for any ITree implementation."""

    def __init__(self, tree):
        self.tree = tree

    # ------------------------------------------------------------------

    def breadth_first(self) -> list:
        root = self.tree.get_root()
        if root is None:
            return []
        result = []
        queue = deque([root])
        while queue:
            node = queue.popleft()
            result.append(node)
            if node.left_child:
                queue.append(node.left_child)
            if node.right_child:
                queue.append(node.right_child)
        return result

    def pre_order(self) -> list:
        result = []
        self._pre(self.tree.get_root(), result)
        return result

    def in_order(self) -> list:
        result = []
        self._in(self.tree.get_root(), result)
        return result

    def post_order(self) -> list:
        result = []
        self._post(self.tree.get_root(), result)
        return result

    # ------------------------------------------------------------------

    def _pre(self, node, acc):
        if node is None:
            return
        acc.append(node)
        self._pre(node.left_child, acc)
        self._pre(node.right_child, acc)

    def _in(self, node, acc):
        if node is None:
            return
        self._in(node.left_child, acc)
        acc.append(node)
        self._in(node.right_child, acc)

    def _post(self, node, acc):
        if node is None:
            return
        self._post(node.left_child, acc)
        self._post(node.right_child, acc)
        acc.append(node)
