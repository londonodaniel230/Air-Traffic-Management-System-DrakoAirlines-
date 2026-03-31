"""
RotationStats — tracks and reports AVL rotation statistics by type.
Single Responsibility: only counts rotations.
"""


class RotationStats:
    """Records rotation counts categorized by type."""

    def __init__(self):
        self.left = 0
        self.right = 0
        self.left_right = 0
        self.right_left = 0
        self.total_cancellations = 0

    def increment(self, rotation_type: str):
        """Increment a rotation counter. Types: left, right, left_right, right_left."""
        if hasattr(self, rotation_type):
            setattr(self, rotation_type, getattr(self, rotation_type) + 1)

    def increment_cancellation(self):
        self.total_cancellations += 1

    def get_total_rotations(self) -> int:
        return self.left + self.right + self.left_right + self.right_left

    def get_summary(self) -> dict:
        return {
            "left": self.left,
            "right": self.right,
            "left_right": self.left_right,
            "right_left": self.right_left,
            "total_rotations": self.get_total_rotations(),
            "total_cancellations": self.total_cancellations,
        }

    def reset(self):
        self.left = 0
        self.right = 0
        self.left_right = 0
        self.right_left = 0
        self.total_cancellations = 0
