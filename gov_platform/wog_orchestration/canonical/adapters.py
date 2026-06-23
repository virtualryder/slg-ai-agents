"""
Canonical adapters + registry — the agency-to-canonical translation boundary.

Every agency models a resident, an address, and a case differently. The canonical
schema (canonical/schema.py) is the agreed contract; an AgencyAdapter maps that
agency's system-of-record record SHAPE to/from the canonical shape. The
orchestrator and every agent reason over ONE representation; only the adapter at
each agency boundary knows the local shape. New agency, new adapter — no change
to the orchestrator or any agent.

In production, adapters live at the connector boundary; the canonical schema is
governed (Glue/DataZone catalog, Lake Formation access control), and schema
versions are pinned so a downstream change is a reviewed event, not a surprise.
"""
from __future__ import annotations

import abc
from typing import Any, Dict, List, Optional

from .schema import Address, CaseRef, Resident

CANONICAL_SCHEMA_VERSION = "1.0.0"


class AgencyAdapter(abc.ABC):
    agency: str = "base"

    @abc.abstractmethod
    def to_canonical(self, record: Dict[str, Any]) -> Any: ...

    @abc.abstractmethod
    def from_canonical(self, entity: Any) -> Dict[str, Any]: ...


class DMVAdapter(AgencyAdapter):
    agency = "DMV"

    def to_canonical(self, record: Dict[str, Any]) -> Resident:
        addr = record.get("garage_address", {})
        return Resident(
            resident_ref=f"RES-{record.get('customer_no', 'unknown')}",
            display_name=record.get("full_name", ""),
            addresses=[Address(addr.get("street", ""), addr.get("city", ""),
                               addr.get("st", ""), addr.get("zip", ""))] if addr else [],
            assurance_level=record.get("idp_aal", "NONE"),
        )

    def from_canonical(self, entity: Resident) -> Dict[str, Any]:
        a = entity.addresses[0] if entity.addresses else None
        return {"customer_no": entity.resident_ref.replace("RES-", ""),
                "full_name": entity.display_name,
                "garage_address": {"street": a.line1, "city": a.city, "st": a.state, "zip": a.postal_code} if a else {}}


class BenefitsAdapter(AgencyAdapter):
    agency = "HHS"

    def to_canonical(self, record: Dict[str, Any]) -> CaseRef:
        return CaseRef(agency="HHS", case_id=record.get("case_number", ""),
                       program=record.get("program_code", ""), status=record.get("status", ""))

    def from_canonical(self, entity: CaseRef) -> Dict[str, Any]:
        return {"case_number": entity.case_id, "program_code": entity.program, "status": entity.status}


class CanonicalRegistry:
    """Registry of agency adapters + the pinned canonical schema version."""

    def __init__(self, schema_version: str = CANONICAL_SCHEMA_VERSION) -> None:
        self.schema_version = schema_version
        self._adapters: Dict[str, AgencyAdapter] = {}

    def register(self, adapter: AgencyAdapter) -> None:
        self._adapters[adapter.agency] = adapter

    def adapter(self, agency: str) -> Optional[AgencyAdapter]:
        return self._adapters.get(agency)

    @property
    def agencies(self) -> List[str]:
        return sorted(self._adapters)


def default_registry() -> CanonicalRegistry:
    r = CanonicalRegistry()
    r.register(DMVAdapter())
    r.register(BenefitsAdapter())
    return r
