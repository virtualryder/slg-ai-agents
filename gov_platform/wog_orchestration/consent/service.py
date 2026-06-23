"""
Consent + identity-assurance ledger.

No cross-agency data use happens without a recorded, scoped, time-bound consent
at a sufficient identity-assurance level (NIST SP 800-63 AAL). The ledger is
append-only (same posture as the gateway audit). A material action that needs a
higher assurance level than the resident currently holds is refused — fail closed.
"""
from __future__ import annotations

import datetime as _dt
import uuid
from dataclasses import dataclass
from typing import Dict, List, Optional

_AAL_ORDER = {"NONE": 0, "AAL1": 1, "AAL2": 2, "AAL3": 3}


@dataclass
class ConsentDecision:
    allowed: bool
    reason: str
    consent_id: Optional[str] = None


class ConsentLedger:
    def __init__(self) -> None:
        self._records: List[Dict] = []

    def record(self, resident_ref: str, scope: str, assurance_level: str,
               ttl_days: int = 365) -> str:
        cid = f"CNS-{uuid.uuid4().hex[:8]}"
        self._records.append({
            "consent_id": cid, "resident_ref": resident_ref, "scope": scope,
            "assurance_level": assurance_level,
            "granted_at": _dt.datetime.now(_dt.timezone.utc).isoformat(),
            "expires": (_dt.date.today() + _dt.timedelta(days=ttl_days)).isoformat(),
        })
        return cid

    def check(self, resident_ref: str, scope: str, required_aal: str = "AAL2") -> ConsentDecision:
        need = _AAL_ORDER.get(required_aal, 99)
        for r in reversed(self._records):
            if r["resident_ref"] == resident_ref and r["scope"] == scope:
                have = _AAL_ORDER.get(r["assurance_level"], 0)
                if have < need:
                    return ConsentDecision(False,
                        f"assurance {r['assurance_level']} < required {required_aal}")
                if r["expires"] < _dt.date.today().isoformat():
                    return ConsentDecision(False, "consent expired", r["consent_id"])
                return ConsentDecision(True, "valid consent", r["consent_id"])
        return ConsentDecision(False, f"no consent on file for scope {scope!r}")

    @property
    def records(self) -> List[Dict]:
        return list(self._records)
