"""
Scored eval metrics for Agent 01 (Resident Services / 311) — the hero pilot.

Where run_evals.py answers "does the artifact keep its required shape?" (binary,
structural regression), this module answers "how GOOD is the agent, on a labeled
benchmark, against thresholds a public-services quality owner would set?"

The predictions are produced by the REAL ingestion pipeline — the NYC 311
connector mapping (NYC311Connector._map_record) and its deterministic
complaint-category classifier (classify_category) — so this scores actual
extraction/classification quality, not a stub. Grounding reuses
governance/grounding.py; PII-leak reuses the platform masker (slg_agent_platform.pii).

Metrics (aggregated over the golden set), with regulatory-weighted thresholds:
  complaint_type_accuracy  >= 0.90   (route the request to the right service line)
  entity_f1                >= 0.85   (complaint_type / agency / borough extraction)
  duplicate_accuracy       >= 0.90   (dedupe requests, don't split or merge wrongly)
  grounding_rate           >= 0.90   (resident-facing summary traceable to the record)
  pii_leak_rate            == 0.00   (HARD GATE — any unmasked identifier fails)
  field_completeness       >= 0.95   (required 311 fields present)
"""
from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple

_REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_REPO))
sys.path.insert(0, str(_REPO / "platform_core"))

from governance.grounding import verify_grounding                          # noqa: E402
from slg_agent_platform.connectors.nyc311 import NYC311Connector, classify_category  # noqa: E402
from slg_agent_platform.pii import mask                                    # noqa: E402

THRESHOLDS: Dict[str, float] = {
    "complaint_type_accuracy": 0.90,
    "entity_f1": 0.85,
    "duplicate_accuracy": 0.90,
    "grounding_rate": 0.90,
    "pii_leak_rate": 0.0,          # <= (hard gate: must be exactly 0)
    "field_completeness": 0.95,
}
# Direction: most metrics are "higher is better" (>=); pii_leak_rate is "<=".
LOWER_IS_BETTER = {"pii_leak_rate"}

# Required 311 fields the record must carry to be actionable/auditable.
_REQUIRED_FIELDS = ["request_id", "complaint_type", "agency", "borough", "status", "created_date"]
# Identifier detector for the PII-leak gate (SSN, email) — mirrors the masker's targets.
_PII = re.compile(r"\b\d{3}-\d{2}-\d{4}\b|[\w.+-]+@[\w-]+\.[\w.]+")


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", str(s)).strip().lower()


def _set(xs: List[str]) -> Set[str]:
    return {_norm(x) for x in xs if x}


@dataclass
class RequestPrediction:
    request_id: str
    category: str
    complaint_type: str
    agency: str
    borough: str
    address: str
    summary: str
    record: Dict[str, Any]


def predict(raw_record: Dict[str, Any]) -> RequestPrediction:
    """Produce the agent's prediction for a 311 record:
      * entity extraction + summary -> the real NYC 311 connector mapping
      * complaint category          -> the real deterministic classifier
        (classify_category), the 311 analog of Agent 02's seriousness assessor.
    """
    rec = NYC311Connector._map_record(raw_record)
    # The classifier is embedded in the mapping (rec["category"]); call it
    # explicitly too so the "real classifier" is unambiguously the prediction.
    category = classify_category(rec["complaint_type"], rec["descriptor"])
    return RequestPrediction(
        request_id=rec["request_id"], category=category,
        complaint_type=rec["complaint_type"], agency=rec["agency"],
        borough=rec["borough"], address=rec["address"],
        summary=rec["summary"], record=rec,
    )


def _prf(tp: int, fp: int, fn: int) -> Tuple[float, float, float]:
    p = tp / (tp + fp) if (tp + fp) else 1.0
    r = tp / (tp + fn) if (tp + fn) else 1.0
    f1 = 2 * p * r / (p + r) if (p + r) else 0.0
    return p, r, f1


def score_dataset(cases: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    cases: list of {"id", "record": {raw 311 fields}, "gold": {category,
           complaint_type, agency, borough, is_duplicate?, dup_of?}}.
    Returns metrics + per-case detail.
    """
    cls_correct = 0
    e_tp = e_fp = e_fn = 0
    grounded = 0
    pii_leaks = 0
    completeness_scores: List[float] = []
    detail: List[Dict[str, Any]] = []

    preds: Dict[str, RequestPrediction] = {}
    for c in cases:
        pred = predict(c["record"])
        preds[c["id"]] = pred
        gold = c["gold"]

        # complaint-type (category) classification
        correct = _norm(pred.category) == _norm(gold["category"])
        cls_correct += 1 if correct else 0

        # entities: (complaint_type, agency, borough) as one micro-set
        gold_ents = _set([gold.get("complaint_type", ""), gold.get("agency", ""),
                          gold.get("borough", "")])
        pred_ents = _set([pred.complaint_type, pred.agency, pred.borough])
        e_tp += len(gold_ents & pred_ents)
        e_fp += len(pred_ents - gold_ents)
        e_fn += len(gold_ents - pred_ents)

        # grounding on the composed summary
        g = verify_grounding(pred.summary, pred.record)
        is_grounded = not (g.ungrounded_numbers or g.ungrounded_entities)
        grounded += 1 if is_grounded else 0

        # PII-leak: the emitted (masked) summary must carry no identifier
        emitted = mask(pred.summary)
        leaked = bool(_PII.search(emitted))
        pii_leaks += 1 if leaked else 0

        # completeness — a field is "present" if populated. NOTE: test PRESENCE
        # (not None/""/[]/{}) NOT truthiness, so a legitimately falsy value would
        # still count as present.
        present = sum(1 for f in _REQUIRED_FIELDS if pred.record.get(f) not in (None, "", [], {}))
        completeness_scores.append(present / len(_REQUIRED_FIELDS))

        detail.append({"id": c["id"], "category_gold": gold["category"],
                       "category_pred": pred.category, "correct": correct,
                       "grounded": is_grounded, "pii_leak": leaked})

    # duplicate detection: gold cases carry is_duplicate + dup_of; predict by
    # shared complaint_type + address between the case and its referenced pair.
    dup_correct = dup_total = 0
    for c in cases:
        if "is_duplicate" not in c["gold"]:
            continue
        dup_total += 1
        gold_dup = bool(c["gold"]["is_duplicate"])
        ref = c["gold"].get("dup_of")
        pred_dup = False
        if ref and ref in preds:
            a, b = preds[c["id"]], preds[ref]
            pred_dup = bool(a.complaint_type and a.complaint_type == b.complaint_type
                            and a.address and a.address == b.address)
        if pred_dup == gold_dup:
            dup_correct += 1

    _, _, e_f1 = _prf(e_tp, e_fp, e_fn)
    n = len(cases)
    metrics = {
        "complaint_type_accuracy": round(cls_correct / n, 4) if n else 1.0,
        "entity_f1": round(e_f1, 4),
        "duplicate_accuracy": round(dup_correct / dup_total, 4) if dup_total else 1.0,
        "grounding_rate": round(grounded / n, 4) if n else 1.0,
        "pii_leak_rate": round(pii_leaks / n, 4) if n else 0.0,
        "field_completeness": round(sum(completeness_scores) / n, 4) if n else 1.0,
    }
    return {"metrics": metrics, "n_cases": n, "detail": detail,
            "classification": {"correct": cls_correct, "total": n}}


def gate(metrics: Dict[str, float]) -> Tuple[bool, List[str]]:
    """Return (passed, failures) against THRESHOLDS."""
    failures: List[str] = []
    for name, thr in THRESHOLDS.items():
        val = metrics.get(name, 0.0)
        if name in LOWER_IS_BETTER:
            if val > thr:
                failures.append(f"{name}={val} exceeds max {thr}")
        elif val < thr:
            failures.append(f"{name}={val} below min {thr}")
    return (not failures), failures
