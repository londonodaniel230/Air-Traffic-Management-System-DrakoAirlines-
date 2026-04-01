"""
VersionManager — named snapshots of the tree state.
Uses TreeSerializer for deep-copy serialization.
"""

import copy
from datetime import datetime


class TreeVersion:
    """Immutable snapshot of a tree at a point in time."""

    def __init__(self, name: str, tree_snapshot: dict, metrics: dict | None = None):
        self.name = name
        self.timestamp = datetime.now()
        self.tree_snapshot = tree_snapshot
        self.metrics = metrics or {}

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "timestamp": self.timestamp.isoformat(),
            "metrics": self.metrics,
        }


class VersionManager:
    """Stores and restores named tree versions."""

    def __init__(self, serializer):
        self._versions: dict[str, TreeVersion] = {}
        self.serializer = serializer

    def save_version(self, name: str, tree, metrics=None) -> TreeVersion:
        snapshot = copy.deepcopy(self.serializer.serialize_tree(tree))
        version = TreeVersion(name, snapshot, metrics)
        self._versions[name] = version
        return version

    def restore_version(self, name: str):
        if name not in self._versions:
            raise ValueError(f"Version '{name}' not found")
        snap = self._versions[name].tree_snapshot
        return self.serializer.deserialize_topology(snap)

    def list_versions(self) -> list:
        return [v.to_dict() for v in self._versions.values()]

    def delete_version(self, name: str):
        self._versions.pop(name, None)

    def version_exists(self, name: str) -> bool:
        return name in self._versions
