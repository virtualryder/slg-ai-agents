# agent/graph.py
# ============================================================
# LangGraph DAG for the Resident Services & 311 workflow.
#
#   intake -> classify_intent -> retrieve_knowledge -> check_identity ->
#   draft_answer -> compliance_check -> [routing] ->
#       { draft_answer (revise, bounded) | human_review_gate } ->
#   finalize -> END
#
# HITL is framework-enforced: the graph compiles with
# interrupt_before=["human_review_gate"], so a city reviewer must update state
# (approval / identity verified / escalate) and resume before finalize runs. No
# application code path reaches finalize without passing through the gate.
# ============================================================
from __future__ import annotations

from langgraph.graph import END, StateGraph

from agent.nodes import (
    intake, classify_intent, retrieve_knowledge, check_identity,
    draft_answer, compliance_check, routing_decision, set_recommended_action, finalize,
)
from agent.persistence import get_checkpointer
from agent.state import ResidentServicesState


def build_resident_services_graph(use_memory: bool = True):
    wf = StateGraph(ResidentServicesState)

    wf.add_node("intake", intake)
    wf.add_node("classify_intent", classify_intent)
    wf.add_node("retrieve_knowledge", retrieve_knowledge)
    wf.add_node("check_identity", check_identity)
    wf.add_node("draft_answer", draft_answer)
    wf.add_node("compliance_check", compliance_check)
    wf.add_node("human_review_gate", set_recommended_action)
    wf.add_node("finalize", finalize)

    wf.set_entry_point("intake")
    wf.add_edge("intake", "classify_intent")
    wf.add_edge("classify_intent", "retrieve_knowledge")
    wf.add_edge("retrieve_knowledge", "check_identity")
    wf.add_edge("check_identity", "draft_answer")
    wf.add_edge("draft_answer", "compliance_check")
    wf.add_conditional_edges(
        source="compliance_check",
        path=routing_decision,
        path_map={"draft_answer": "draft_answer", "human_review_gate": "human_review_gate"},
    )
    wf.add_edge("human_review_gate", "finalize")
    wf.add_edge("finalize", END)

    if use_memory:
        return wf.compile(checkpointer=get_checkpointer(),
                          interrupt_before=["human_review_gate"])
    return wf.compile()


def get_graph_visualization() -> str:
    return """
graph TD
    A[Resident Request] --> B[intake]
    B --> C[classify_intent]
    C --> D[retrieve_knowledge<br/>kb.search_policy]
    D --> E[check_identity<br/>identity.verify_resident]
    E --> F[draft_answer<br/>grounded + cited]
    F --> G[compliance_check<br/>grounding · WCAG · PII]
    G --> H{routing_decision}
    H -->|issues, revise| F
    H -->|clean / verify / escalate| I[human_review_gate<br/>City Reviewer]
    I --> J[finalize<br/>311 create · book · answer]
    J --> K[END]
    style I fill:#4CAF50,color:#fff
    style K fill:#2196F3,color:#fff
"""
