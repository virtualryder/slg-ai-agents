# Scoped Pilot SOW — Governed Resident Services / 311 Agent on AWS

*Template statement of work for a time-boxed, low-risk pilot proving the governed pattern in the
agency's AWS account. Reference accelerator — not an AWS service, not StateRAMP/FedRAMP-authorized;
see [`NOT-CLAIMS.md`](../NOT-CLAIMS.md). Template for scoping, not a signed agreement or legal advice.*

## 1. Objective

Prove, in the agency's AWS account, that an AI agent can **safely** help resident-services staff:
classify an inbound 311 request, retrieve grounded answers from approved policy content, and draft a
response or a service request — **with a human reviewing every write** and immutable evidence for every
step. Deliberately narrow: **one workflow, one connector path, one approval path, one evidence report.**

## 2. Duration & shape

**6–10 weeks**: Foundation (1–3) → Governed pilot (3–8) → Evidence & readout (8–10). Public open data
and/or synthetic resident records only; no CJI and no production city-system write in the pilot.

## 3. Agency prerequisites (before week 1)

- An AWS account (or sandbox OU) with Amazon Bedrock + the required model in a supported Region (GovCloud if required).
- An identity provider (Okta / Entra / AD) and the resident-services role group.
- A named **reviewer** (the public servant who approves writes) and a business owner for go/no-go.
- Security contact (KMS key policy, VPC, Guardrail settings).
- **Data:** approved public policy/FAQ content to index, plus **synthetic** resident requests. No CJI.

## 4. Scope — in

- Deploy the 311 golden path (SAM) into the agency account: MCP gateway, Step Functions workflow with
  the `waitForTaskToken` human gate, append-only + S3 Object-Lock audit, PII/CJI masking, token budget,
  Bedrock + Guardrails over PrivateLink.
- **One connector path:** the **tier-3 NYC 311 Socrata live reference** read (public), OR a **tier-2
  local HTTP stand-in** shaped like the agency's 311/CRM.
- Wire the agency IdP + the resident-services role; exercise the human-approval gate on any create/update.
- Run the governed workflow end-to-end on synthetic requests; produce the immutable audit evidence.
- Run the 10-point negative demo (`make neg-demo`) in the agency account as an acceptance gate.

## 5. Scope — out (explicitly)

- **Production connector to ServiceNow / Salesforce / a custom 311 CRM (tier-4)** — separate SOW.
- Any CJI-touching workflow (separated, entitled environment; separate engagement).
- ATO / StateRAMP / FedRAMP authorization, penetration test, production monitoring, DR, operations.
- Real writes to a production city system of record.

## 6. Success metrics (agreed before week 3)

- **Governance:** 10/10 negative-demo refusals enforced in the agency account.
- **Human authority:** every create/update blocks at the reviewer gate; the agent never mutates the city system on its own.
- **Grounding:** drafted answers trace to the approved policy corpus (no ungrounded claims).
- **Throughput (illustrative, to be baselined):** median handling time for a triaged request vs. the manual baseline.
- **Evidence:** a complete append-only audit trail for every pilot request, exported as the evidence pack.

## 7. Security gates (must pass to proceed to readout)

Deny-by-default gateway live; bound single-use SoD approvals; scoped short-lived tokens; fail-closed
PII/CJI masking; append-only + WORM audit; Bedrock reached only over PrivateLink with no egress to
external AI APIs. Reviewed against [`ASSURANCE-PACKET.md`](ASSURANCE-PACKET.md) and
[`../docs/THREAT-MODEL.md`](../docs/THREAT-MODEL.md).

## 8. Deployment path

Canonical: the **SAM golden path** (`infra/golden-path-311/`) — `sam build && sam deploy` + smoke test
+ teardown. Hardened option: the `-secure` variant (in-VPC Lambdas, PrivateLink, CMK, S3 Object-Lock,
CloudFront/WAF). Runbook: [`docs/DEPLOY-RUNBOOK.md`](docs/DEPLOY-RUNBOOK.md).

## 9. Deliverables

1. Deployed governed 311 golden path in the agency account.
2. Evidence pack: clean-account acceptance, the negative-demo result, and the per-request audit export.
3. A go/no-go readout with the success-metric results and a scoped path to production (CRM connector, ATO, IdP, monitoring).

## 10. Go / no-go criteria

**Go** if: all security gates pass, 10/10 refusals enforced, the human gate held on every write, and the
grounding/throughput metrics meet the agreed thresholds. **No-go / iterate** if any security gate fails
or the human-authority boundary is not demonstrably enforced.

## 11. Shared responsibility

Per [`ASSURANCE-PACKET.md` §8](ASSURANCE-PACKET.md) and
[`../docs/PRODUCTION-READINESS-AND-SHARED-RESPONSIBILITY.md`](../docs/PRODUCTION-READINESS-AND-SHARED-RESPONSIBILITY.md).
The accelerator provides the governed control plane; the agency owns identity, production connectors,
authorization, and operations.
