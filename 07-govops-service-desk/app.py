# app.py — Streamlit dashboard for GovOps IT Service Desk & Modernization (demo mode).
import os, sys
from pathlib import Path
os.environ.setdefault("EXTRACT_MODE","demo")
_REPO=Path(__file__).resolve().parent.parent
sys.path[:0]=[str(_REPO/"platform_core"),str(_REPO),str(Path(__file__).resolve().parent)]
import streamlit as st  # noqa: E402
from agent.core import run_until_gate, resume  # noqa: E402
st.set_page_config(page_title="GovOps IT Service Desk & Modernization", page_icon="🏛️", layout="wide")
st.title("🏛️ GovOps IT Service Desk & Modernization")
CLAIMS={"sub":"staff-1","custom:slg_role":"IT_ANALYST"}
q=st.text_input("Request","how do i")
if st.button("Run"):
    s=run_until_gate({"raw_request":q,"acting_user_claims":CLAIMS})
    st.write("Intent:",s.get("intent"),"· Action:",str(s.get("recommended_action")))
    st.write("Grounded:",s.get("grounding_report",{}).get("grounded")); st.json(s.get("artifact",{}))
    st.info("Paused at human review gate — a reviewer approves before any write executes.")
