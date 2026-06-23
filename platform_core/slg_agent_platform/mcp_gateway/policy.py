"""
MCP authorization policy — the heart of the AgentCore Gateway decision for SLG.

Deny-by-default with **least privilege as an intersection**: a tool call is
permitted only if BOTH the calling agent is granted the tool AND the acting
government user is entitled to it. An agent can never do more than the public
servant on whose behalf it acts — even if the agent's own grant list is broader.

  permitted(tool) ⇔ tool ∈ AGENT_TOOL_GRANTS[agent] ∩ ⋃ ROLE_ENTITLEMENTS[user_roles]

High-risk (write / irreversible) tools additionally require a human approval
record before execution. Reads do not. The legally consequential actions in SLG
(issue a permit, adjudicate eligibility, release a public-records package, award
a contract, run a destructive IT operation) are modeled as high-risk and, in
several cases, deliberately *withheld* from the agent entirely so a human owns
the decision.

In production these tables are expressed as Amazon Bedrock AgentCore Gateway
targets + AgentCore Identity scopes (or API Gateway + Lambda authorizer + STS +
Cognito + Cedar/OPA) fed by the agency IdP. Here they are explicit Python so the
intersection semantics are testable and unambiguous. Tool names
("<connector_kind>.<operation>") map 1:1 to AgentCore Gateway target names.

References: Bedrock AgentCore Gateway / Identity
  https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/gateway.html
  https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/identity.html
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, FrozenSet, Iterable, List, Tuple

# ── Tool registry: tool name -> (connector_kind, method, high_risk) ───────────
# high_risk=True => write/irreversible => human-approval gate before execution.
TOOL_REGISTRY: Dict[str, Tuple[str, str, bool]] = {
    # Resident services / 311 / CRM
    "crm311.get_service_request":    ("crm311", "get_service_request", False),
    "crm311.search_requests":        ("crm311", "search_requests", False),
    "crm311.create_service_request": ("crm311", "create_service_request", True),   # write
    "crm311.update_service_request": ("crm311", "update_service_request", True),    # write
    # Grounded knowledge (approved public content / policy manuals)
    "kb.search_policy":              ("kb", "search_policy", False),
    "kb.get_article":                ("kb", "get_article", False),
    # Identity + consent (authenticated, personalized answers)
    "identity.verify_resident":      ("identity", "verify_resident", False),
    "consent.check":                 ("consent", "check", False),
    "consent.record":                ("consent", "record", True),                   # write
    # Scheduling / appointments
    "scheduling.get_availability":   ("scheduling", "get_availability", False),
    "scheduling.book_appointment":   ("scheduling", "book_appointment", True),       # write
    # GIS / parcel / location
    "gis.get_parcel":                ("gis", "get_parcel", False),
    # Forms / intelligent document processing
    "idp.extract_document":          ("idp", "extract_document", False),
    "idp.validate_form":             ("idp", "validate_form", False),
    "idp.assemble_form":             ("idp", "assemble_form", True),                 # write
    # Permitting / licensing (Accela / Tyler / custom)
    "permitting.get_permit":         ("permitting", "get_permit", False),
    "permitting.check_requirements": ("permitting", "check_requirements", False),
    "permitting.create_application": ("permitting", "create_application", True),     # write
    "permitting.route_review":       ("permitting", "route_review", True),           # write
    "permitting.issue_permit":       ("permitting", "issue_permit", True),           # write/irreversible
    # Benefits / human services eligibility (integrated eligibility system)
    "eligibility.screen":            ("eligibility", "screen", False),               # deterministic prescreen
    "eligibility.get_case":          ("eligibility", "get_case", False),
    "eligibility.create_application":("eligibility", "create_application", True),    # write
    "eligibility.generate_notice":   ("eligibility", "generate_notice", True),       # write (draft notice)
    "eligibility.adjudicate":        ("eligibility", "adjudicate", True),            # write/irreversible
    # Public records / FOIA / redaction
    "records.search":                ("records", "search", False),
    "records.classify":              ("records", "classify", False),
    "records.propose_redaction":     ("records", "propose_redaction", False),
    "records.assemble_package":      ("records", "assemble_package", True),          # write
    "records.release":               ("records", "release", True),                  # write/irreversible
    # Procurement / contracting / grants
    "procurement.search_contracts":  ("procurement", "search_contracts", False),
    "procurement.draft_rfp":         ("procurement", "draft_rfp", True),             # write
    "procurement.compare_bids":      ("procurement", "compare_bids", False),         # organizes evidence only
    "procurement.award":             ("procurement", "award", True),                # write/irreversible
    # IT service desk / operations / modernization
    "itsm.get_ticket":               ("itsm", "get_ticket", False),
    "itsm.create_ticket":            ("itsm", "create_ticket", True),                # write
    "itsm.run_runbook":              ("itsm", "run_runbook", True),                  # write/high-risk
    # Public safety / public health (CJI / PHI separated environments)
    "safety.summarize_incident":     ("safety", "summarize_incident", False),
    "safety.draft_report":           ("safety", "draft_report", True),               # write (draft)
    "phsurveillance.run_query":      ("phsurveillance", "run_query", False),         # validated SQL only
}

HIGH_RISK_TOOLS: FrozenSet[str] = frozenset(t for t, (_, _, hr) in TOOL_REGISTRY.items() if hr)

# ── What each AGENT is allowed to call (its job description as code) ───────────
# Note the deliberate omissions: agents may PREPARE but not COMMIT the legally
# consequential action. e.g. the permitting agent cannot issue_permit; the
# procurement agent cannot award; the records agent cannot release; the benefits
# agent cannot adjudicate. Those grants live only with human-held roles.
AGENT_TOOL_GRANTS: Dict[str, FrozenSet[str]] = {
    "01-resident-services-311": frozenset({
        "crm311.get_service_request", "crm311.search_requests", "crm311.create_service_request",
        "kb.search_policy", "kb.get_article",
        "identity.verify_resident", "consent.check",
        "scheduling.get_availability", "scheduling.book_appointment", "gis.get_parcel",
    }),
    "02-forms-idp": frozenset({
        "idp.extract_document", "idp.validate_form", "idp.assemble_form",
        "kb.search_policy", "identity.verify_resident", "consent.check", "consent.record",
        "crm311.create_service_request",
    }),
    "03-permitting-licensing": frozenset({
        "permitting.get_permit", "permitting.check_requirements", "permitting.create_application",
        "permitting.route_review", "gis.get_parcel", "kb.search_policy", "idp.extract_document",
    }),  # NOTE: no permitting.issue_permit — issuance is a human official decision
    "04-benefits-caseworker": frozenset({
        "eligibility.screen", "eligibility.get_case", "eligibility.create_application",
        "eligibility.generate_notice", "idp.extract_document", "kb.search_policy",
        "identity.verify_resident", "consent.check",
    }),  # NOTE: no eligibility.adjudicate — determination is deterministic engine + human
    "05-public-records-foia": frozenset({
        "records.search", "records.classify", "records.propose_redaction",
        "records.assemble_package", "kb.search_policy",
    }),  # NOTE: no records.release — disclosure is a records officer decision
    "06-procurement-grants": frozenset({
        "procurement.search_contracts", "procurement.draft_rfp", "procurement.compare_bids",
        "kb.search_policy", "idp.extract_document",
    }),  # NOTE: no procurement.award — award is a procurement officer decision
    "07-govops-service-desk": frozenset({
        "itsm.get_ticket", "itsm.create_ticket", "itsm.run_runbook", "kb.search_policy",
    }),
    "08-public-safety-health": frozenset({
        "safety.summarize_incident", "safety.draft_report", "phsurveillance.run_query",
        "kb.search_policy",
    }),
}

# ── What each USER ROLE is entitled to (the public servant's real permissions) ─
ROLE_ENTITLEMENTS: Dict[str, FrozenSet[str]] = {
    "RESIDENT_SERVICES_AGENT": frozenset({
        "crm311.get_service_request", "crm311.search_requests", "crm311.create_service_request",
        "kb.search_policy", "kb.get_article", "identity.verify_resident", "consent.check",
        "scheduling.get_availability", "scheduling.book_appointment", "gis.get_parcel",
    }),
    "INTAKE_SPECIALIST": frozenset({
        "idp.extract_document", "idp.validate_form", "idp.assemble_form",
        "kb.search_policy", "identity.verify_resident", "consent.check", "consent.record",
        "crm311.create_service_request",
    }),
    "PERMIT_TECH": frozenset({
        "permitting.get_permit", "permitting.check_requirements", "permitting.create_application",
        "permitting.route_review", "gis.get_parcel", "kb.search_policy", "idp.extract_document",
    }),
    "PERMIT_OFFICIAL": frozenset({  # tech + the irreversible issuance authority
        "permitting.get_permit", "permitting.check_requirements", "permitting.create_application",
        "permitting.route_review", "permitting.issue_permit", "gis.get_parcel", "kb.search_policy",
        "idp.extract_document",
    }),
    "ELIGIBILITY_CASEWORKER": frozenset({
        "eligibility.screen", "eligibility.get_case", "eligibility.create_application",
        "eligibility.generate_notice", "idp.extract_document", "kb.search_policy",
        "identity.verify_resident", "consent.check",
    }),
    "ELIGIBILITY_SUPERVISOR": frozenset({  # caseworker + the irreversible adjudication
        "eligibility.screen", "eligibility.get_case", "eligibility.create_application",
        "eligibility.generate_notice", "eligibility.adjudicate", "idp.extract_document",
        "kb.search_policy", "identity.verify_resident", "consent.check",
    }),
    "RECORDS_TECH": frozenset({
        "records.search", "records.classify", "records.propose_redaction",
        "records.assemble_package", "kb.search_policy",
    }),
    "RECORDS_OFFICER": frozenset({  # tech + the irreversible public release
        "records.search", "records.classify", "records.propose_redaction",
        "records.assemble_package", "records.release", "kb.search_policy",
    }),
    "PROCUREMENT_ANALYST": frozenset({
        "procurement.search_contracts", "procurement.draft_rfp", "procurement.compare_bids",
        "kb.search_policy", "idp.extract_document",
    }),
    "PROCUREMENT_OFFICER": frozenset({  # analyst + the irreversible award
        "procurement.search_contracts", "procurement.draft_rfp", "procurement.compare_bids",
        "procurement.award", "kb.search_policy", "idp.extract_document",
    }),
    "IT_ANALYST": frozenset({
        "itsm.get_ticket", "itsm.create_ticket", "kb.search_policy",
    }),
    "IT_SRE": frozenset({  # analyst + approved runbook execution
        "itsm.get_ticket", "itsm.create_ticket", "itsm.run_runbook", "kb.search_policy",
    }),
    "PUBLIC_SAFETY_ANALYST": frozenset({
        "safety.summarize_incident", "safety.draft_report", "kb.search_policy",
    }),
    "PUBLIC_HEALTH_EPIDEMIOLOGIST": frozenset({
        "phsurveillance.run_query", "kb.search_policy",
    }),
}


@dataclass
class PolicyDecision:
    allowed: bool
    tool: str
    reason: str
    requires_approval: bool = False
    connector_kind: str = ""
    method: str = ""
    effective_scope: List[str] = field(default_factory=list)  # exactly this tool


def user_entitlements(roles: Iterable[str]) -> FrozenSet[str]:
    out: set = set()
    for r in roles:
        out |= ROLE_ENTITLEMENTS.get(r, frozenset())
    return frozenset(out)


def decide(agent_id: str, user_roles: Iterable[str], tool: str) -> PolicyDecision:
    """Deny-by-default authorization with least-privilege intersection."""
    if tool not in TOOL_REGISTRY:
        return PolicyDecision(False, tool, f"unknown tool {tool!r}")

    connector_kind, method, high_risk = TOOL_REGISTRY[tool]
    agent_grants = AGENT_TOOL_GRANTS.get(agent_id, frozenset())
    if tool not in agent_grants:
        return PolicyDecision(False, tool,
                              f"agent {agent_id!r} is not granted {tool!r} (agent over-reach denied)",
                              connector_kind=connector_kind, method=method)

    ent = user_entitlements(user_roles)
    if tool not in ent:
        return PolicyDecision(False, tool,
                              f"acting user (roles={list(user_roles)}) is not entitled to {tool!r} "
                              f"(an agent may never exceed the user's own permissions)",
                              connector_kind=connector_kind, method=method)

    return PolicyDecision(
        True, tool,
        "permitted by agent grant ∩ user entitlement",
        requires_approval=tool in HIGH_RISK_TOOLS,
        connector_kind=connector_kind, method=method,
        effective_scope=[tool],
    )
