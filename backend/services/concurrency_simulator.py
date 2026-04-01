"""
ConcurrencySimulator — FIFO queue of insertion requests that can be
processed step-by-step (simulated concurrency).
"""

from datetime import datetime
from collections import deque


class InsertionRequest:
    """A single queued flight-insertion request."""

    def __init__(self, flight_data: dict):
        self.flight_data = flight_data
        self.timestamp = datetime.now()

    def to_dict(self) -> dict:
        return {
            "flight_data": self.flight_data,
            "timestamp": self.timestamp.isoformat(),
        }


class InsertionQueue:
    """FIFO queue for InsertionRequest objects."""

    def __init__(self):
        self._q: deque[InsertionRequest] = deque()

    def enqueue(self, request: InsertionRequest):
        self._q.append(request)

    def dequeue(self) -> InsertionRequest:
        if self.is_empty():
            raise ValueError("Queue is empty")
        return self._q.popleft()

    def is_empty(self) -> bool:
        return len(self._q) == 0

    def size(self) -> int:
        return len(self._q)

    def get_pending(self) -> list:
        return [r.to_dict() for r in self._q]

    def clear(self):
        self._q.clear()


class ConcurrencySimulator:
    """Processes InsertionQueue requests one-by-one through FlightManager."""

    def __init__(self, flight_manager):
        self.queue = InsertionQueue()
        self.flight_manager = flight_manager

    def schedule_insertion(self, flight_data: dict) -> dict:
        req = InsertionRequest(flight_data)
        self.queue.enqueue(req)
        return req.to_dict()

    def process_next(self) -> dict:
        if self.queue.is_empty():
            return {"status": "empty", "message": "No pending requests"}
        req = self.queue.dequeue()
        try:
            node = self.flight_manager.create_flight(req.flight_data)
            return {
                "status": "success",
                "flight": node.to_dict(),
                "remaining": self.queue.size(),
            }
        except Exception as exc:
            return {
                "status": "error",
                "message": str(exc),
                "flight_data": req.flight_data,
                "remaining": self.queue.size(),
            }

    def process_all(self) -> list:
        results = []
        while not self.queue.is_empty():
            results.append(self.process_next())
        return results

    def get_queue_status(self) -> dict:
        return {
            "size": self.queue.size(),
            "pending": self.queue.get_pending(),
        }
