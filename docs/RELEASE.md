# Releasing & cloud integration verification (P9)

Two workflows turn the offline guarantees into **verified cloud evidence** and a versioned release.

## 1. Ephemeral-AWS integration test (`.github/workflows/integration.yml`)
Proves the **deployed, authenticated** surface enforces the governance the unit suite models.

**Trigger:** manual (`workflow_dispatch`) — it provisions real infrastructure, so it is gated on
credentials rather than running on every PR.

**Prerequisites (one-time):**
- An IAM role assumable by this repo via **GitHub OIDC**, stored as the repo secret
  `AWS_OIDC_ROLE_ARN`. It needs permissions to `sam deploy`/`sam delete` the golden path and to
  run the tests (CloudFormation, Lambda, Step Functions, Cognito admin, DynamoDB, IAM, API
  Gateway, S3 for the SAM artifact bucket).

**What it does:** `sam build` + `sam deploy` an **ephemeral** stack (`slg-it-<run-id>`) →
installs `boto3`/`pycognito` → runs `tests/integration -m integration` → **always** `sam delete`.

**What the tests assert** (`tests/integration/test_authenticated_api.py`, real Cognito JWT via
SRP):
| Check | Expectation |
|---|---|
| unauthenticated request | `401` (no JWT) |
| unauthorized tool (agent not granted) | `403` `DENY` |
| entitled read (`kb.search_policy`) | `200` `ALLOW` + `audit_id` |
| high-risk write, no approval | `202` `PENDING_APPROVAL`, no result |
| reviewer approves same pending twice | 2nd `403/409` (durable single-use) |
| approve once → workflow | `REQUEST_CREATED` + `request_id` (fixture created) |
| audit table | row count `> 0` (attempts were audited) |

Run locally against a stack you deployed yourself:
```bash
SLG_STACK=slg-311-dev AWS_REGION=us-east-1 \
  PYTHONPATH=platform_core:. pytest tests/integration -m integration -q
```
(The tests **skip** automatically when `SLG_STACK` is unset, so the offline suite is unaffected.)

## 2. Tagged release (`.github/workflows/release.yml`)
On a `v*` tag: re-runs the **hard gates** (unit tests, cfn-lint, bandit), generates a CycloneDX
**SBOM**, and publishes a **GitHub Release** whose notes are the matching `CHANGELOG.md` section.

```bash
git tag v0.1.0 && git push origin v0.1.0
```
The current version is in `VERSION` (**0.1.0** — first tagged reference release).

## Honest status
The pipelines are committed and the tests are real, but a **green run requires a connected AWS
account**; attaching that run is the final piece of cloud evidence. Everything else (offline
suite, cfn-lint, bandit, SBOM, secret scan) runs with no credentials on every push.
