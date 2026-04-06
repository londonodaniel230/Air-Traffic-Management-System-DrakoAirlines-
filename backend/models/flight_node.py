"""
FlightNode — represents a single flight in the tree.
Implements ISerializable for JSON persistence.
"""

from models.interfaces import ISerializable


class FlightNode(ISerializable):
    """Node representing a flight with all associated data and tree pointers."""

    def __init__(self, flight_code, origin, destination, base_price,
                 passengers, promotion=0.0, priority=1, alerts=None,
                 departure_time=""):
        # --- Flight data ---
        self.flight_code = str(flight_code)
        self.origin = str(origin)
        self.destination = str(destination)
        self.departure_time = str(departure_time)
        self.base_price = float(base_price)
        self.passengers = int(passengers)
        self.promotion = float(promotion) if not isinstance(promotion, bool) else 0.0
        self.priority = int(priority)
        self.alerts = alerts if isinstance(alerts, list) else ([] if not alerts else ["alerta activa"])

        # --- Computed / state ---
        self.penalty = 0.0
        self.is_critical = False
        self.final_price = self.base_price

        # --- Tree structure ---
        self.height = 1
        self.balance_factor = 0
        self.parent = None
        self.left_child = None
        self.right_child = None

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def is_leaf(self) -> bool:
        return self.left_child is None and self.right_child is None

    def get_profitability(self) -> float:
        """profitability = passengers * finalPrice - promotion + penalty."""
        return self.passengers * self.final_price - self.promotion + self.penalty

    # ------------------------------------------------------------------
    # Mutations
    # ------------------------------------------------------------------

    def update_final_price(self):
        """Recalculate final_price from base, penalty and promotion."""
        self.final_price = self.base_price + self.penalty - self.promotion
        self.final_price = max(0.0, self.final_price)

    def copy_data_from(self, other: "FlightNode"):
        """Copy only flight payload (not tree pointers) from another node."""
        self.flight_code = other.flight_code
        self.origin = other.origin
        self.destination = other.destination
        self.departure_time = other.departure_time
        self.base_price = other.base_price
        self.final_price = other.final_price
        self.passengers = other.passengers
        self.promotion = other.promotion
        self.penalty = other.penalty
        self.is_critical = other.is_critical
        self.priority = other.priority
        self.alerts = list(other.alerts)

    def clone(self) -> "FlightNode":
        """Deep-copy of flight data without tree relationships."""
        node = FlightNode(
            self.flight_code, self.origin, self.destination,
            self.base_price, self.passengers, self.promotion,
            self.priority, list(self.alerts), self.departure_time,
        )
        node.penalty = self.penalty
        node.is_critical = self.is_critical
        node.final_price = self.final_price
        return node

    # ------------------------------------------------------------------
    # Serialization (ISerializable)
    # ------------------------------------------------------------------

    def to_dict(self) -> dict:
        return {
            "flight_code": self.flight_code,
            "origin": self.origin,
            "destination": self.destination,
            "departure_time": self.departure_time,
            "base_price": self.base_price,
            "final_price": self.final_price,
            "passengers": self.passengers,
            "promotion": self.promotion,
            "penalty": self.penalty,
            "is_critical": self.is_critical,
            "priority": self.priority,
            "alerts": list(self.alerts),
            "height": self.height,
            "balance_factor": self.balance_factor,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "FlightNode":
        # Handle boolean promotion / alerts from Spanish-format JSON
        promo = data.get("promotion", 0.0)
        if isinstance(promo, bool):
            promo = 0.0
        alerts = data.get("alerts", [])
        if isinstance(alerts, bool):
            alerts = ["alerta activa"] if alerts else []

        node = cls(
            data["flight_code"],
            data["origin"],
            data["destination"],
            data["base_price"],
            data["passengers"],
            promo,
            data.get("priority", 1),
            alerts,
            data.get("departure_time", ""),
        )
        node.penalty = data.get("penalty", 0.0)
        node.is_critical = data.get("is_critical", False)
        node.final_price = data.get("final_price", node.base_price)
        node.height = data.get("height", 1)
        node.balance_factor = data.get("balance_factor", 0)
        return node

    # ------------------------------------------------------------------

    def __repr__(self):
        return f"FlightNode({self.flight_code})"
