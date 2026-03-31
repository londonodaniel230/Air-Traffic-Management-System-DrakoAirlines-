"""
Interfaces for the SkyBalance AVL system.
Follows Interface Segregation Principle (ISP) from SOLID.
"""

from abc import ABC, abstractmethod


class ITree(ABC):
    """Contract for tree data structures (BST, AVL)."""

    @abstractmethod
    def insert(self, node):
        """Insert a node into the tree."""

    @abstractmethod
    def delete(self, flight_code: str):
        """Delete a node by flight code."""

    @abstractmethod
    def search(self, flight_code: str):
        """Search for a node by flight code."""

    @abstractmethod
    def get_root(self):
        """Return the root node."""

    @abstractmethod
    def get_height(self) -> int:
        """Return the height of the tree."""

    @abstractmethod
    def get_leaf_count(self) -> int:
        """Return the number of leaf nodes."""

    @abstractmethod
    def is_empty(self) -> bool:
        """Return True if the tree has no nodes."""


class ITraversable(ABC):
    """Contract for tree traversal operations."""

    @abstractmethod
    def breadth_first(self) -> list:
        """Breadth-first (level order) traversal."""

    @abstractmethod
    def pre_order(self) -> list:
        """Pre-order depth traversal (Root-Left-Right)."""

    @abstractmethod
    def in_order(self) -> list:
        """In-order depth traversal (Left-Root-Right)."""

    @abstractmethod
    def post_order(self) -> list:
        """Post-order depth traversal (Left-Right-Root)."""


class ISerializable(ABC):
    """Contract for objects that can be serialized to/from dict."""

    @abstractmethod
    def to_dict(self) -> dict:
        """Serialize to dictionary."""

    @classmethod
    @abstractmethod
    def from_dict(cls, data: dict):
        """Deserialize from dictionary."""
