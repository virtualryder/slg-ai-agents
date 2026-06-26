# Golden Path 311 — Architecture, Bill of Materials & IAM Matrix

## Architecture (deployed by `infra/golden-path-311/template.yaml`, SAM)
```
Resident/staff ─HTTPS─► HTTP API (Cognito JWT authorizer · access logs · throttling)
                              │ POST /tool/{kind}/{method}
                              ▼
                        Connector Lambda ──► systems of record (fixture | live)
Step Functions state machine (the agent):
   Classify ─► Draft ─► Check ─► [ HUMAN GATE: waitForTaskToken ] ─► Finalize
     (each step = a Lambda; shared layer = platform_core + governance + core)
Bedrock (Claude) + Guardrails (input+output)  ◄─ via account; Guardrail scoped
Audit: DynamoDB (PITR, KMS)   ·   Identity: Cognito (MFA, advanced security)
Logs: CloudWatch (gateway access + state-machine execution)
```

## Bill of materials (AWS resources)
| Resource | Type | Purpose | Notes |
|---|---|---|---|
| `SharedLayer` | Lambda LayerVersion | platform_core + governance + agent core | makefile build |
| `ClassifyFn / DraftFn / CheckFn / FinalizeFn / HitlNotifyFn` | Lambda | the 5 workflow steps | per-function role |
| `ConnectorFn` | Lambda | governed connector (gateway target) | fixture or live |
| `ResidentStateMachine` | Step Functions | the agent; human gate = `waitForTaskToken` | exec logging ALL |
| `GatewayApi` | API Gateway HTTP API | front door | JWT authorizer + throttling |
| `ResidentGuardrail` | Bedrock Guardrail | PII + prompt-attack (in/out) | denied topics |
| `UserPool / UserPoolClient` | Cognito | identity | MFA on; immutable role; 15-min tokens |
| `AuditTable` | DynamoDB | audit | PITR + SSE; Retain |
| `GatewayAccessLogs / StateMachineLogs` | CloudWatch Logs | observability | 365-day retention |

## IAM least-privilege matrix
| Principal (role) | Allowed actions | Scoped to | Denied / not granted |
|---|---|---|---|
| `DraftFn` | `bedrock:InvokeModel` | the **model ARN** only | everything else |
| `CheckFn` | `bedrock:ApplyGuardrail` | the **guardrail ARN** only | model invoke, data |
| `FinalizeFn` | `dynamodb:PutItem` | the **audit table ARN** only | Update/Delete |
| `ClassifyFn / HitlNotifyFn` | basic execution (logs) | — | any data/model |
| `ConnectorFn` | basic execution (+ connector creds via Secrets Manager in live) | named secret | broad data access |
| State machine | `lambda:InvokeFunction` | the **5 agent functions** | any other function |
| (generic stack) Runtime role | bedrock model+guardrail, KMS | model/guardrail/key ARNs | `Resource:"*"` |
| (generic stack) Audit-writer policy | `dynamodb:PutItem` | audit table | **explicit deny** Update/Delete/BatchWrite |

Source: `infra/golden-path-311/template.yaml`, `infra/cloudformation/security.yaml`, `infra/cloudformation/data.yaml`.
