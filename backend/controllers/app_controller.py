"""
AppController — single orchestrator that wires every service together
and exposes the public API consumed by Flask routes.
"""

from models.avl_tree import AVLTree
from services.flight_manager import FlightManager
from services.traversal_service import TraversalService
from services.tree_serializer import TreeSerializer
from services.version_manager import VersionManager
from services.concurrency_simulator import ConcurrencySimulator
from services.metrics_engine import MetricsEngine
from services.depth_penalty_system import DepthPenaltySystem
from services.avl_auditor import AVLAuditor
from services.profitability_analyzer import ProfitabilityAnalyzer
from services.json_normalizer import JSONNormalizer


class AppController:
    """Façade that the Flask layer calls.  No HTTP concepts here."""

    def __init__(self):
        self.avl_tree = AVLTree()
        self.bst_comparison = None          # only set after insertion-load
        self.normalizer = JSONNormalizer()
        self.serializer = TreeSerializer()
        self.penalty_system = DepthPenaltySystem(self.avl_tree)
        self.flight_manager = FlightManager(self.avl_tree, self.penalty_system)
        self.traversal = TraversalService(self.avl_tree)
        self.metrics = MetricsEngine(self.avl_tree, self.traversal)
        self.version_manager = VersionManager(self.serializer)
        self.concurrency = ConcurrencySimulator(self.flight_manager)
        self.auditor = AVLAuditor(self.avl_tree)
        self.profitability = ProfitabilityAnalyzer(self.avl_tree)

    # ------------------------------------------------------------------
    # helpers
    # ------------------------------------------------------------------

    def _rebuild_services(self):
        """Re-wire services after the tree reference changes."""
        cd = self.penalty_system.critical_depth
        self.penalty_system = DepthPenaltySystem(self.avl_tree, cd)
        self.flight_manager = FlightManager(self.avl_tree, self.penalty_system)
        self.traversal = TraversalService(self.avl_tree)
        self.metrics = MetricsEngine(self.avl_tree, self.traversal)
        self.concurrency = ConcurrencySimulator(self.flight_manager)
        self.auditor = AVLAuditor(self.avl_tree)
        self.profitability = ProfitabilityAnalyzer(self.avl_tree)

    # ------------------------------------------------------------------
    # Load / Export
    # ------------------------------------------------------------------

    def load_from_json(self, data: dict, mode: str = "topology") -> dict:
        # Normalize Spanish-format JSON if needed
        data = self.normalizer.normalize(data)
        mode = data.get("load_mode", mode)
        cd = data.get("critical_depth", self.penalty_system.critical_depth)

        if mode == "topology":
            self.avl_tree = self.serializer.deserialize_topology(data)
            self.bst_comparison = None
        else:
            self.avl_tree, self.bst_comparison = (
                self.serializer.deserialize_insertion(data)
            )

        self._rebuild_services()
        self.penalty_system.set_critical_depth(cd)

        result = {"avl": self.get_tree_state()}
        if self.bst_comparison:
            bst_trav = TraversalService(self.bst_comparison)
            result["bst"] = {
                "height": self.bst_comparison.get_height(),
                "size": self.bst_comparison.size,
                "tree": self.serializer.serialize_tree(self.bst_comparison),
                "in_order": [n.to_dict() for n in bst_trav.in_order()],
            }
        return result

    def export_tree(self) -> dict:
        return self.serializer.serialize_tree(self.avl_tree)

    # ------------------------------------------------------------------
    # Flight CRUD
    # ------------------------------------------------------------------

    def create_flight(self, data: dict) -> dict:
        return self.flight_manager.create_flight(data).to_dict()

    def modify_flight(self, code: str, data: dict) -> dict:
        return self.flight_manager.modify_flight(code, data).to_dict()

    def delete_flight(self, code: str) -> dict:
        return self.flight_manager.delete_flight(code)

    def cancel_flight(self, code: str) -> dict:
        sub = self.flight_manager.cancel_flight(code)
        return {"cancelled_nodes": sub, "count": len(sub)}

    # ------------------------------------------------------------------
    # Undo
    # ------------------------------------------------------------------

    def undo(self) -> dict:
        return self.flight_manager.undo()

    # ------------------------------------------------------------------
    # Smart delete
    # ------------------------------------------------------------------

    def smart_delete(self) -> dict:
        node = self.profitability.find_least_profitable()
        if node is None:
            raise ValueError("Tree is empty")
        prof = self.profitability.calculate(node)
        sub = self.flight_manager.cancel_flight(node.flight_code)
        return {
            "target": node.flight_code,
            "profitability": prof,
            "cancelled_nodes": sub,
            "count": len(sub),
        }

    # ------------------------------------------------------------------
    # Versions
    # ------------------------------------------------------------------

    def save_version(self, name: str) -> dict:
        m = self.metrics.get_dashboard_data()
        return self.version_manager.save_version(name, self.avl_tree, m).to_dict()

    def restore_version(self, name: str) -> dict:
        self.avl_tree = self.version_manager.restore_version(name)
        self._rebuild_services()
        return self.get_tree_state()

    def list_versions(self) -> list:
        return self.version_manager.list_versions()

    # ------------------------------------------------------------------
    # Queue / Concurrency
    # ------------------------------------------------------------------

    def schedule_insertion(self, data: dict) -> dict:
        return self.concurrency.schedule_insertion(data)

    def process_next(self) -> dict:
        return self.concurrency.process_next()

    def process_all(self) -> list:
        return self.concurrency.process_all()

    def get_queue_status(self) -> dict:
        return self.concurrency.get_queue_status()

    # ------------------------------------------------------------------
    # Stress mode
    # ------------------------------------------------------------------

    def toggle_stress(self) -> dict:
        return {"stress_mode": self.avl_tree.toggle_stress_mode()}

    def global_rebalance(self) -> dict:
        self.avl_tree.stress_mode = False
        report = self.avl_tree.global_rebalance()
        self.penalty_system.recalculate_all_prices()
        return report

    # ------------------------------------------------------------------
    # Audit
    # ------------------------------------------------------------------

    def audit(self) -> dict:
        return self.auditor.verify_avl_property().to_dict()

    # ------------------------------------------------------------------
    # Metrics / Traversals
    # ------------------------------------------------------------------

    def get_metrics(self) -> dict:
        return self.metrics.get_dashboard_data()

    def get_traversals(self) -> dict:
        return self.metrics.get_all_traversals()

    # ------------------------------------------------------------------
    # Penalty
    # ------------------------------------------------------------------

    def set_critical_depth(self, depth: int) -> dict:
        self.penalty_system.set_critical_depth(depth)
        return {"critical_depth": depth}

    # ------------------------------------------------------------------
    # Profitability
    # ------------------------------------------------------------------

    def get_profitability_ranking(self) -> list:
        return self.profitability.get_ranking()

    # ------------------------------------------------------------------
    # Full state
    # ------------------------------------------------------------------

    def get_tree_state(self) -> dict:
        return {
            "tree": self.serializer.serialize_tree(self.avl_tree),
            "metrics": self.metrics.get_dashboard_data(),
            "can_undo": self.flight_manager.can_undo(),
            "undo_history": self.flight_manager.get_undo_history(),
            "critical_depth": self.penalty_system.critical_depth,
        }
