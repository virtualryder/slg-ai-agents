# Golden Path 311 — Cost Estimate, Known Limitations & Shared Responsibility

## Indicative pilot cost (order-of-magnitude, us-east-1, serverless)
*Illustrative for a low-volume pilot (e.g. ~50k tool calls / month). Confirm with the AWS Pricing Calculator for the customer's volume and region; GovCloud differs.*

| Service | Driver | Indicative monthly (pilot) |
|---|---|---|
| Amazon Bedrock (Claude) | per-token, ~50k short calls | $$ (volume-driven; the dominant variable) |
| Lambda (6 functions) | per-invoke + GB-s, serverless | low (often < $20) |
| Step Functions | state transitions | low (< $25 at pilot volume) |
| API Gateway (HTTP API) | per-request | low (< $5) |
| DynamoDB (on-demand) | audit writes + PITR | low (< $25) |
| S3 Object Lock (WORM) | evidence storage + retention | low; grows with retention |
| Cognito | MAUs (advanced security adds per-MAU) | low at pilot scale |
| KMS + CloudWatch Logs | keys + log retention | low (< $20) |

**Takeaway:** at pilot scale the cost is **dominated by Bedrock token usage**; the governed infrastructure is inexpensive and serverless (scales to zero). Set Bedrock budget alarms (customer-owned) per `OWASP-LLM-ATLAS-MAPPING.md` LLM10.

## Known limitations (what this golden path is NOT, yet)
- **Connectors are fixtures by default** — `ConnectorMode=live` requires building + validating real agency adapters (the largest engagement line item).
- **WAF** is applied at the **CloudFront edge** (`edge.yaml`); WAFv2 does not attach directly to HTTP APIs.
- **Egress allowlisting** (Network Firewall / endpoint policies) is a documented optional overlay, not yet in this template.
- **No ATO / StateRAMP / FedRAMP authorization** and **no third-party pen test** — engagement work.
- **Token signing** uses dev HMAC by default; production swaps to KMS-held asymmetric / AgentCore Identity.
- **DR**: PITR + WORM are present; multi-Region (global tables, multi-Region KMS) is an additive overlay.

## Shared responsibility (summary; full RACI: `docs/PRODUCTION-READINESS-AND-SHARED-RESPONSIBILITY.md`)
| Layer | AWS | Delivery Partner / SA | Customer (agency) |
|---|---|---|---|
| Authorized cloud + services | ✔ (FedRAMP High / IL-4/5 in GovCloud) | — | — |
| Deploy + configure the golden path | — | ✔ | review |
| Live connectors + validation | — | ✔ build | ✔ own systems |
| IdP federation + entitlements | — | assist | ✔ |
| Data classification + retention schedule | — | advise | ✔ |
| ATO / StateRAMP, pen test, model-risk | — | assist | ✔ |
| Day-2 ops + HITL queue staffing | — | assist | ✔ |

**Recommended first agent:** a low-blast-radius workflow (Resident Services / 311 or IT service desk) — **not** Benefits or Public Safety first.
