"""
Canonical data layer — the shared vocabulary across agencies.

The single largest obstacle to whole-of-government service is not the model; it is
that every agency models a resident, an address, and a case differently. These
canonical definitions are the agreed contract. Each agency maps its system of
record to/from these shapes at its connector boundary, so the orchestrator and
every agent reason over ONE representation. Fields are intentionally minimal and
privacy-conscious: identifiers are references (tokens), never raw SSNs.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class Address:
    line1: str
    city: str
    state: str
    postal_code: str
    parcel_id: Optional[str] = None


@dataclass(frozen=True)
class Consent:
    scope: str                 # e.g. "address_update", "status_lookup", "cross_agency_share"
    granted: bool
    assurance_level: str       # NIST 800-63 AAL: NONE | AAL1 | AAL2 | AAL3
    expires: Optional[str] = None


@dataclass(frozen=True)
class CaseRef:
    agency: str                # owning agency / system
    case_id: str
    program: Optional[str] = None
    status: Optional[str] = None


@dataclass
class Resident:
    resident_ref: str          # opaque token, NOT an SSN
    display_name: str = ""
    addresses: List[Address] = field(default_factory=list)
    consents: List[Consent] = field(default_factory=list)
    cases: List[CaseRef] = field(default_factory=list)
    assurance_level: str = "NONE"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ServiceEvent:
    """A canonical record of a material step, for the compliance event bus."""
    event_type: str            # e.g. "address.updated", "application.created"
    resident_ref: str
    agency: str
    agent_id: str
    summary: str
    requires_confirmation: bool = False


def canonical_resident(resident_ref: str, **kw: Any) -> Resident:
    return Resident(resident_ref=resident_ref, **kw)


def validate(resident: Resident) -> List[str]:
    """Return a list of contract violations (empty == valid)."""
    errs: List[str] = []
    if not resident.resident_ref or "-" not in resident.resident_ref:
        errs.append("resident_ref must be an opaque token (no raw identifiers)")
    if any(len(a.state) != 2 for a in resident.addresses):
        errs.append("address.state must be a 2-letter code")
    valid_aal = {"NONE", "AAL1", "AAL2", "AAL3"}
    if resident.assurance_level not in valid_aal:
        errs.append(f"assurance_level must be one of {valid_aal}")
    return errs
