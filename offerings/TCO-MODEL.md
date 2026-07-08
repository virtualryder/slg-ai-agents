# TCO Model — SLG AI Agent Suite
### Monthly AWS run-cost model: Pilot vs Production

> **MODEL ASSUMPTION — illustrative estimate** built from published us-east-1 on-demand list
> prices as of mid-2026; prices and token economics change frequently; validate with the AWS
> Pricing Calculator and your AWS account team before quoting. **Bedrock token volume is the
> dominant, workload-dependent variable** — every Bedrock line below is the sensitivity driver.
> No figure here is a quote.

This is the suite cost model referenced by each agent's `docs/roi-analysis.md`. It replaces the
previously referenced `COST-ROI-MODEL.md` — run cost and the ROI-netting worksheet live in this
single file. Value-side inputs (deflection rates, loaded contact costs) stay in the per-agent
`docs/roi-analysis.md` worksheets.

---

## Scenario assumptions

| Assumption | **Pilot** (1 agent, dept-scale) | **Production** (8-agent suite) |
|---|---|---|
| Governed requests/month | ~15,000 (311 is the highest-volume SLG entry point) | ~750,000 |
| Active users (MAU) | ~50 staff | ~2,000 staff (residents hit the public channel, not Cognito) |
| Bedrock tokens/month | ~6M input + ~1.2M output | ~300M input + ~60M output |
| Model class | Mid-tier Claude (Sonnet-class): ~$3.00/M input, ~$15.00/M output tokens `[MODEL ASSUMPTION]` | same |
| Architecture | Serverless reference path (API Gateway HTTP API → Lambda → Step Functions → Bedrock), private-by-default (VPC interface endpoints even in pilot) | same, plus production hardening (NAT, WAF, CloudFront) |
| Per-request shape | ~2 API calls, ~5 Lambda invocations, ~15 Step Functions state transitions, ~10 DynamoDB writes + 20 reads (audit + state) | same |

311 interactions are short (grounded FAQ answer + routing), so tokens-per-request are lower than
document-heavy verticals; the volume is what's high. Adjust both to the customer's actual contact
volume before presenting.

## Monthly cost estimate (us-east-1, on-demand list, mid-2026)

| Line item | Basis | **Pilot ($/mo)** | **Production ($/mo)** |
|---|---|---:|---:|
| **Bedrock inference** ← *sensitivity driver* | Sonnet-class; 6M in + 1.2M out (pilot) / 300M in + 60M out (prod) | **36** | **1,800** |
| Bedrock Guardrails ← *scales with request volume* | Content filters, prompt-side; ~1.5 text units/request @ ~$0.75/1K units | 17 | 844 |
| Lambda | ~5 invocations/request; 512 MB × ~800 ms | 1 | 26 |
| API Gateway (HTTP API) | ~2 calls/request @ ~$1.00/M | 1 | 2 |
| Step Functions (Standard) | ~15 state transitions/request @ ~$25/M | 6 | 281 |
| DynamoDB (on-demand) | ~10 WRU + 20 RRU/request + storage (1 GB pilot / 25 GB prod) | 1 | 13 |
| S3 + Object Lock (WORM audit) | 5 GB pilot / 200 GB prod + requests | 2 | 7 |
| KMS | $1/CMK (4 pilot / 6 prod) + ~20 requests/request @ $0.03/10K | 5 | 51 |
| Cognito | MAU-based (~$0.015/MAU); 50 pilot / 2,000 prod | 1 | 30 |
| CloudWatch | Logs ingest + metrics + dashboards | 3 | 50 |
| VPC interface endpoints | ~$7.30/endpoint-mo + data; 5 endpoints pilot / 8 prod (Bedrock, KMS, STS, Logs, Secrets…) | 36 | 68 |
| NAT Gateway | Prod only; ~$33/mo + ~100 GB processed | — | 37 |
| WAF | Prod only; web ACL + 5 rules + request fees | — | 11 |
| CloudFront | Prod only; public 311 channel, low-GB tier | — | 10 |
| **TOTAL** | | **~$109/mo** | **~$3,230/mo** |

**Sensitivity (one line):** 2× Bedrock token volume ≈ **+$1,800/mo** at production scale
(inference is >55% of the production total); every other line moves slowly.

Rounding: whole dollars; sub-dollar lines shown as $1. Annualized production: ~$38.8K/yr.

## What's NOT included

- Personnel (program owner, reviewers, platform operations)
- ProServe / SI partner delivery fees (Assessment, POC, Pilot — see engagement pricing)
- Data egress at scale (cross-Region, bulk export)
- AWS enterprise support plan (typically 3–10% of spend)
- Non-prod environments (dev/test/staging — commonly +30–60% of the prod infra baseline, minimal Bedrock in demo mode)

## ROI netting (worksheet)

```
Net monthly value = (avoided live contacts × loaded cost/contact)   ← per-agent docs/roi-analysis.md
                  − monthly AWS run cost (this model)
                  − monthly share of SI fees / managed service
```

Example: Agent 01 at the roi-analysis example inputs ($1.5M/yr gross benefit = $125K/mo) against
the full production suite run cost (~$3.2K/mo) — run cost is ~2.6% of modeled gross benefit.
The business case is decided by the deflection assumption, not the AWS bill.

---

*Related: per-agent `docs/roi-analysis.md`, `ENTERPRISE-PLATFORM.md`, `docs/`. Demand-side
statistics are source-tagged in `SOURCES.md`.*

---
**Value side:** see [ROI-CASE-STUDY.md](ROI-CASE-STUDY.md) for a fully worked, illustrative ROI example with totals.
