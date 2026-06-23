"""
Whole-of-Government (WoG) Orchestration Platform.

The strategic layer that lets a state or municipality move from dozens of
isolated chatbots to governed digital workers coordinated across agencies. Five
pillars, each a module here:

  1. canonical/  — shared canonical data definitions (one Resident, one Address,
                   one Case shape) so agencies interoperate without point-to-point
                   schema translation.
  2. consent/    — identity-assurance + consent ledger; no cross-agency data use
                   without a recorded, scoped, time-bound consent.
  3. events/     — compliance event bus; every material step emits an immutable,
                   compliance-tagged event for the unified case-level audit trail.
  4. supervisor/ — life-event orchestrator; durable, multi-agency workflows with
                   EXPLICIT resident confirmation before each material action.
  5. govern tool access — inherited from slg_agent_platform.mcp_gateway (the same
                   deny-by-default gateway every specialist agent already uses).

Specialist agents (01–08) plug in as registered handlers; the orchestrator never
holds tool grants and never bypasses a specialist's gateway path.
"""
__version__ = "0.1.0"
