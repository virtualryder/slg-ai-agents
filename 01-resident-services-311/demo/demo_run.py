"""End-to-end demo (no API key). Runs the 311 workflow over the sample requests,
stopping at the human gate and resuming with an approval for write actions."""
from __future__ import annotations

import json
import os
from pathlib import Path

os.environ.setdefault("EXTRACT_MODE", "demo")
import sys
_REPO = Path(__file__).resolve().parent.parent.parent
sys.path[:0] = [str(_REPO / "platform_core"), str(_REPO), str(_REPO / "01-resident-services-311")]

from agent.core import run_until_gate, resume  # noqa: E402

APPROVAL = {"approved": True, "reviewer": {"sub": "supervisor-1", "name": "City Reviewer"}}


def main() -> None:
    samples = json.loads((_REPO / "01-resident-services-311/data/fixtures/sample_requests.json").read_text())
    for req in samples:
        s = run_until_gate(req)
        print(f"\n=== {req['request_id']}: {req['raw_request']}")
        print(f"  intent={s.get('intent')} action={s.get('recommended_action')} "
              f"grounded={s.get('grounding_report',{}).get('grounded')} "
              f"needs_identity={s.get('needs_identity')}")
        final = resume(s, approval=APPROVAL)
        print(f"  -> case_status={final.get('case_status')} "
              f"sr={final.get('service_request_id')} appt={final.get('appointment_id')}")


if __name__ == "__main__":
    main()
