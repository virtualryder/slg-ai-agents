"""Demo (no API key) for Forms & Intelligent Document Processing."""
from __future__ import annotations
import json, os, sys
from pathlib import Path
os.environ.setdefault("EXTRACT_MODE", "demo")
_REPO = Path(__file__).resolve().parent.parent.parent
sys.path[:0] = [str(_REPO/"platform_core"), str(_REPO), str(_REPO/"02-forms-idp")]
from agent.core import run_until_gate, resume  # noqa: E402

APPROVAL = {"approved": True, "reviewer": {"sub": "supervisor-1"}}

def main():
    samples = json.loads((_REPO/"02-forms-idp/data/fixtures/sample_requests.json").read_text())
    for req in samples:
        s = run_until_gate(req)
        final = resume(s, approval=APPROVAL)
        print(f"{req['request_id']:18s} intent={s.get('intent'):14s} "
              f"action={str(s.get('recommended_action'))} -> {final.get('case_status')}")

if __name__ == "__main__":
    main()
