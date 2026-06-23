import sys
from pathlib import Path
_REPO=Path(__file__).resolve().parent.parent.parent
sys.path[:0]=[str(_REPO/"platform_core"),str(_REPO/"02-forms-idp")]
from tools import gateway_tools as gw
CLAIMS={"sub":"staff-1","custom:slg_role":"INTAKE_SPECIALIST"}

def test_read_tool_allowed():
    res=gw.call(CLAIMS, "idp.extract_document", {'doc_type': 'income_statement'})
    assert res.allowed

def test_write_tool_requires_approval():
    res=gw.call(CLAIMS, "idp.assemble_form", {'form_id': 'FORM-1'})
    assert res.decision in ("PENDING_APPROVAL","DENY")
