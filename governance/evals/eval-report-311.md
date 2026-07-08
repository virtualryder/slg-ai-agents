# Agent 01 (Resident Services / 311) — scored eval report

**Result:** PASS · **Cases:** 22 · Predictions from the real NYC 311 connector mapping + deterministic complaint classifier; grounding via `governance/grounding.py`; PII-leak via the platform masker.

| Metric | Value | Threshold | Status |
|---|---|---|---|
| complaint_type_accuracy | 1.0 | >= 0.9 | PASS |
| entity_f1 | 1.0 | >= 0.85 | PASS |
| duplicate_accuracy | 1.0 | >= 0.9 | PASS |
| grounding_rate | 1.0 | >= 0.9 | PASS |
| pii_leak_rate | 0.0 | <= 0.0 | PASS |
| field_completeness | 1.0 | >= 0.95 | PASS |

**Complaint-type classification:** 22/22 correct (the deterministic `classify_category` routing, scored against reviewer labels).

This report is the quality-evidence artifact for the assurance packet: it shows the agent's extraction/classification measured against a labeled 311 benchmark with a **PII-leak hard gate (= 0)**. Regenerate with `python -m governance.evals.score_311`.
