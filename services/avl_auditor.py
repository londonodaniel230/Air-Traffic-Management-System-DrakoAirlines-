"""
AVLAuditor — verifies that every node satisfies the AVL invariant.
Only meaningful in stress mode (where the tree may be degraded).
"""


class AuditIssue:
    """A single inconsistency found during the audit."""

    def __init__(self, flight_code: str, issue_type: str, expected, actual):
        self.flight_code = flight_code
        self.issue_type = issue_type
        self.expected = expected
        self.actual = actual

    def to_dict(self) -> dict:
        return {
            "flight_code": self.flight_code,
            "issue_type": self.issue_type,
            "expected": str(self.expected),
            "actual": str(self.actual),
            "description": self.get_description(),
        }

    def get_description(self) -> str:
        return (
            f"{self.flight_code}: {self.issue_type} — "
            f"expected {self.expected}, got {self.actual}"
        )


class AuditReport:
    """Complete result of an AVL property verification."""

    def __init__(self):
        self.is_valid = True
        self.issues: list[AuditIssue] = []
        self.total_nodes_checked = 0
        self.inconsistent_nodes: list[str] = []

    def add_issue(self, issue: AuditIssue):
        self.issues.append(issue)
        self.is_valid = False
        if issue.flight_code not in self.inconsistent_nodes:
            self.inconsistent_nodes.append(issue.flight_code)

    def to_dict(self) -> dict:
        return {
            "is_valid": self.is_valid,
            "total_nodes_checked": self.total_nodes_checked,
            "inconsistent_count": len(self.inconsistent_nodes),
            "inconsistent_nodes": self.inconsistent_nodes,
            "issues": [i.to_dict() for i in self.issues],
            "summary": self.get_summary(),
        }

    def get_summary(self) -> str:
        if self.is_valid:
            return f"AVL VALID — {self.total_nodes_checked} nodes verified."
        return (
            f"AVL INVALID — {len(self.issues)} issue(s) in "
            f"{len(self.inconsistent_nodes)} node(s) "
            f"({self.total_nodes_checked} checked)."
        )


class AVLAuditor:
    """Walks the tree and produces an AuditReport."""

    def __init__(self, tree):
        self.tree = tree

    def verify_avl_property(self) -> AuditReport:
        report = AuditReport()
        self._check(self.tree.get_root(), report)
        return report

    def _check(self, node, report: AuditReport) -> int:
        """Returns computed height; adds issues to *report*."""
        if node is None:
            return 0

        report.total_nodes_checked += 1

        left_h = self._check(node.left_child, report)
        right_h = self._check(node.right_child, report)

        expected_h = 1 + max(left_h, right_h)
        if node.height != expected_h:
            report.add_issue(
                AuditIssue(node.flight_code, "incorrect_height",
                           expected_h, node.height)
            )

        expected_bf = left_h - right_h
        if node.balance_factor != expected_bf:
            report.add_issue(
                AuditIssue(node.flight_code, "incorrect_balance_factor",
                           expected_bf, node.balance_factor)
            )

        if expected_bf not in (-1, 0, 1):
            report.add_issue(
                AuditIssue(node.flight_code, "avl_violation",
                           "{-1, 0, 1}", expected_bf)
            )

        return expected_h
