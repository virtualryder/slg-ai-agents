# agent/graph.py — Permitting & Licensing
# LangGraph StateGraph with a framework-enforced HITL interrupt before the gate.
from __future__ import annotations
from langgraph.graph import END, StateGraph
from agent.nodes import (intake, classify_intent, check_identity, gather, produce,
                        compliance_check, routing_decision, set_recommended_action, finalize)
from agent.persistence import get_checkpointer
from agent.state import AgentState


def build_graph(use_memory: bool = True):
    wf = StateGraph(AgentState)
    for n, fn in [("intake", intake), ("classify_intent", classify_intent),
                  ("check_identity", check_identity), ("gather", gather), ("produce", produce),
                  ("compliance_check", compliance_check),
                  ("human_review_gate", set_recommended_action), ("finalize", finalize)]:
        wf.add_node(n, fn)
    wf.set_entry_point("intake")
    wf.add_edge("intake", "classify_intent"); wf.add_edge("classify_intent", "check_identity")
    wf.add_edge("check_identity", "gather"); wf.add_edge("gather", "produce")
    wf.add_edge("produce", "compliance_check")
    wf.add_conditional_edges("compliance_check", routing_decision,
                             {"produce": "produce", "human_review_gate": "human_review_gate"})
    wf.add_edge("human_review_gate", "finalize"); wf.add_edge("finalize", END)
    if use_memory:
        return wf.compile(checkpointer=get_checkpointer(), interrupt_before=["human_review_gate"])
    return wf.compile()
