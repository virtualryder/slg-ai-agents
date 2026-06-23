# app.py — Streamlit reference dashboard for Procurement, Contracting & Grants (demo mode).
from __future__ import annotations
import os, sys
from pathlib import Path
os.environ.setdefault("EXTRACT_MODE", "demo")
_REPO = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(_REPO/"platform_core"), str(_REPO), str(Path(__file__).resolve().parent)]
import streamlit as st  # noqa: E402
from agent.core import run_until_gate, resume  # noqa: E402

st.set_page_config(page_title="Procurement, Contracting & Grants", page_icon="🏛️", layout="wide")
st.title("🏛️ Procurement, Contracting & Grants")
st.caption("Governed AI on AWS — grounded, human-approved, audited.")
CLAIMS = {"sub": "staff-1", "custom:slg_role": "PROCUREMENT_ANALYST"}
q = st.text_input("Request", "Help me with this case.")
if st.button("Run workflow"):
    s = run_until_gate({"raw_request": q, "acting_user_claims": CLAIMS})
    st.write("Intent:", s.get("intent")); st.write("Recommended action:", str(s.get("recommended_action")))
    st.write("Grounded:", s.get("grounding_report", {}).get("grounded"))
    st.json(s.get("artifact", {}))
    st.info("Paused at human review gate. A reviewer approves before any write executes.")
