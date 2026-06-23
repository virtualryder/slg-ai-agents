"""Demo (no API key) for Permitting & Licensing."""
import json, os, sys
from pathlib import Path
os.environ.setdefault("EXTRACT_MODE","demo")
_REPO=Path(__file__).resolve().parent.parent.parent
sys.path[:0]=[str(_REPO/"platform_core"),str(_REPO),str(_REPO/"03-permitting-licensing")]
from agent.core import run_until_gate, resume  # noqa: E402
APPROVAL={"approved":True,"reviewer":{"sub":"supervisor-1"}}
def main():
    for req in json.loads((_REPO/"03-permitting-licensing/data/fixtures/sample_requests.json").read_text()):
        s=run_until_gate(req); final=resume(s, approval=APPROVAL)
        print(f"{req['request_id']:16s} intent={s.get('intent'):14s} action={str(s.get('recommended_action')):28s} -> {final.get('case_status')}")
if __name__=="__main__": main()
