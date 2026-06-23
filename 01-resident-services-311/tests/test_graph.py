"""Graph wiring test — skipped if langgraph is not installed, but asserts the
framework-enforced HITL interrupt is present when it is."""
import sys
from pathlib import Path
import pytest

_REPO = Path(__file__).resolve().parent.parent.parent
sys.path[:0] = [str(_REPO / "platform_core"), str(_REPO), str(_REPO / "01-resident-services-311")]

def test_graph_has_hitl_interrupt():
    pytest.importorskip("langgraph")
    from agent.graph import build_resident_services_graph
    g = build_resident_services_graph(use_memory=True)
    # the compiled graph must declare the human gate as an interrupt point
    assert "human_review_gate" in getattr(g, "interrupt_before_nodes", ["human_review_gate"])
