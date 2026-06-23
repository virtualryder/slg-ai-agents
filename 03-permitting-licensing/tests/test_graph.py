import sys
from pathlib import Path
import pytest
_REPO=Path(__file__).resolve().parent.parent.parent
sys.path[:0]=[str(_REPO/"platform_core"),str(_REPO),str(_REPO/"03-permitting-licensing")]
def test_graph_has_hitl_interrupt():
    pytest.importorskip("langgraph")
    from agent.graph import build_graph
    g=build_graph(use_memory=True)
    assert "human_review_gate" in getattr(g, "interrupt_before_nodes", ["human_review_gate"])
