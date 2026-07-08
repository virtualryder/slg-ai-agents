"""
CI gate for the Agent 01 (Resident Services / 311) scored eval + negative controls.

The positive tests hold the quality line on the golden set. The negative controls
prove the gate has TEETH — that the scorers actually catch a misclassified request,
an ungrounded value, and a PII identifier — so a green run means something.
"""
import json
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent.parent))
sys.path.insert(0, str(_HERE.parent.parent / "platform_core"))

from governance.evals import scorers_311  # noqa: E402
from governance.evals.scorers_311 import score_dataset, gate, THRESHOLDS, _PII  # noqa: E402
from governance.grounding import verify_grounding                              # noqa: E402

GOLDEN = _HERE / "golden" / "agent01_311_scored.json"


def _cases():
    return json.loads(GOLDEN.read_text(encoding="utf-8"))["cases"]


# ── positive: the benchmark passes every threshold ───────────────────────────

def test_scored_eval_meets_all_thresholds():
    result = score_dataset(_cases())
    passed, failures = gate(result["metrics"])
    assert passed, f"threshold failures: {failures}"


def test_pii_leak_hard_gate_is_zero():
    result = score_dataset(_cases())
    assert result["metrics"]["pii_leak_rate"] == 0.0


def test_complaint_type_accuracy_meets_bar():
    m = score_dataset(_cases())["metrics"]
    assert m["complaint_type_accuracy"] >= THRESHOLDS["complaint_type_accuracy"]


# ── negative controls: the gate must FAIL on bad data ────────────────────────

def test_gate_catches_a_misclassification():
    # Same record, but the reviewer's gold category disagrees with what the real
    # deterministic classifier produces -> classification accuracy drops below the bar.
    cases = _cases()
    poisoned = json.loads(json.dumps(cases[0]))     # an "Illegal Parking" case
    poisoned["id"] = "MISCLASS"
    poisoned["gold"]["category"] = "Housing"        # wrong: classifier yields Parking/Vehicle
    result = score_dataset([poisoned])
    passed, _ = gate(result["metrics"])
    assert result["metrics"]["complaint_type_accuracy"] < 1.0
    assert not passed                                # the gate rejects it


def test_grounding_scorer_flags_an_ungrounded_value():
    # A summary asserting a value absent from the record must be flagged.
    g = verify_grounding("The fee is $4,250 and the Zoning Appeals Board meets soon.",
                         {"complaint_type": "Illegal Parking", "agency": "NYPD",
                          "borough": "MANHATTAN"})
    assert g.ungrounded_numbers or g.ungrounded_entities, \
        "grounding scorer failed to flag an ungrounded value"


def test_pii_detector_catches_identifiers():
    assert _PII.search("reporter jane.doe@example.com SSN 123-45-6789")
    assert not _PII.search("311 request in MANHATTAN handled by NYPD.")


def test_pii_gate_fails_when_masking_leaks(monkeypatch):
    # If the masker were disabled/broken and a record carried an identifier, the
    # emitted narrative would leak -> pii_leak_rate > 0 -> the hard gate must fail.
    monkeypatch.setattr(scorers_311, "mask", lambda text, *a, **k: text)  # simulate broken masker
    leaky = {"id": "PII", "record": {
        "unique_key": "31199999", "complaint_type": "Illegal Parking",
        "descriptor": "reporter SSN 123-45-6789", "agency": "NYPD",
        "agency_name": "New York City Police Department", "borough": "MANHATTAN",
        "incident_address": "350 5 Avenue", "status": "Open", "created_date": "2024-06-01"},
        "gold": {"category": "Parking/Vehicle", "complaint_type": "Illegal Parking",
                 "agency": "NYPD", "borough": "MANHATTAN"}}
    result = score_dataset([leaky])
    passed, _ = gate(result["metrics"])
    assert result["metrics"]["pii_leak_rate"] > 0.0
    assert not passed
