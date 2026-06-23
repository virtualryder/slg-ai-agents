# app.py — Streamlit reference dashboard for Agent 01 (demo mode, no API key).
from __future__ import annotations
import os, sys
from pathlib import Path

os.environ.setdefault("EXTRACT_MODE", "demo")
_REPO = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(_REPO / "platform_core"), str(_REPO), str(Path(__file__).resolve().parent)]

import streamlit as st  # noqa: E402
from agent.core import run_until_gate, resume  # noqa: E402

st.set_page_config(page_title="Resident Services & 311 Agent", page_icon="🏛️", layout="wide")
st.title("🏛️ Resident Services & 311 Navigator")
st.caption("Governed AI on AWS — grounded answers, identity-gated personal data, human-approved actions.")

CLAIMS = {"sub": "rep-1", "custom:slg_role": "RESIDENT_SERVICES_AGENT"}
q = st.text_input("Resident request", "How do I find out my trash pickup day?")
if st.button("Run workflow"):
    s = run_until_gate({"raw_request": q, "acting_user_claims": CLAIMS})
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Draft answer"); st.write(s.get("draft_answer"))
        st.subheader("Citations")
        for c in s.get("citations", []):
            st.markdown(f"- [{c['title']}]({c['url']})")
    with c2:
        st.metric("Intent", s.get("intent"))
        st.metric("Recommended action", str(s.get("recommended_action")))
        st.metric("Grounded", str(s.get("grounding_report", {}).get("grounded")))
        st.metric("Needs identity", str(s.get("needs_identity")))
        st.subheader("Compliance findings"); st.write(s.get("quality_findings") or "none")
    st.info("⏸️ Paused at human review gate. A city reviewer approves before any write executes.")
    if st.button("Approve & finalize (reviewer)"):
        final = resume(s, {"approved": True, "reviewer": {"sub": "supervisor-1"}})
        st.success(f"Case status: {final.get('case_status')}")
