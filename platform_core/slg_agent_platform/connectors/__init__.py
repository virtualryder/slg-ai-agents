"""Connector framework — typed adapters to SLG systems of record (fixture / live)."""
from .base import Connector, FixtureBackedConnector
from .factory import get_connector

__all__ = ["Connector", "FixtureBackedConnector", "get_connector"]
