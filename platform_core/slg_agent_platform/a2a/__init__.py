"""A2A supervisor — governed cross-agency routing (holds no tool grants)."""
from .supervisor import Supervisor, RouteResult, INTENT_ROUTES, LIFE_EVENTS

__all__ = ["Supervisor", "RouteResult", "INTENT_ROUTES", "LIFE_EVENTS"]
