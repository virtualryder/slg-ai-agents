# Suite Architecture Reference — Six Layers + AWS Service Mapping

```
┌─────────────────────────────────────────────────────────────────────────┐
│  LAYER 6 — GOVERNANCE & OBSERVABILITY                                    │
│  Grounding · Prompt registry · Evals · Red team · Fairness · Accessibility│
│  · Audit · CloudWatch · CloudTrail                                        │
├─────────────────────────────────────────────────────────────────────────┤
│  LAYER 5 — MODELS & DETERMINISTIC SERVICES                               │
│  Bedrock (Claude) · Guardrails · eligibility/fee/scoring engines · masker │
├─────────────────────────────────────────────────────────────────────────┤
│  LAYER 4 — DATA & SEMANTIC LAYER                                         │
│  Knowledge Bases (OpenSearch/Aurora pgvector) · canonical data · GIS · RWD│
├─────────────────────────────────────────────────────────────────────────┤
│  LAYER 3 — TOOL & INTEGRATION (MCP AUTHORIZATION GATEWAY)                │
│  AgentCore Gateway · AgentCore Identity · Connectors · PII/CJI/FTI Masker │
├─────────────────────────────────────────────────────────────────────────┤
│  LAYER 2 — SUPERVISOR & SPECIALIST AGENTS                               │
│  WoG orchestrator · LangGraph specialists · HITL gates                   │
├─────────────────────────────────────────────────────────────────────────┤
│  LAYER 1 — UX IN EXISTING CHANNELS                                      │
│  Web/mobile · chat · voice (Connect optional) · staff consoles · API     │
└─────────────────────────────────────────────────────────────────────────┘
```

## AWS service mapping
| Role | AWS service | Notes |
|---|---|---|
| Agent runtime (container) | **AgentCore Runtime** | ARM64; `/invocations`+`/ping` |
| Agent runtime (native) | **Step Functions + Lambda** | `waitForTaskToken` HITL gate |
| MCP gateway | **AgentCore Gateway** or **API Gateway + Lambda authorizer + STS** | portable path works in **GovCloud** |
| Identity + scoped tokens | **AgentCore Identity + Cognito** | federates agency IdP (SAML/OIDC) |
| LLM inference | **Bedrock (Claude)** | in-account; no PII egress |
| Safety + PII | **Bedrock Guardrails** | PII/denied-topics/grounding |
| Retrieval | **Bedrock Knowledge Bases / Amazon Q Business** | OpenSearch Serverless / Aurora pgvector; ACL-trimmed |
| Append-only audit | **DynamoDB** (deny Update/Delete) + PITR | unified case-level trail |
| WORM records | **S3 Object Lock (COMPLIANCE)** | retention-schedule aligned |
| Encryption | **KMS CMK** | per-environment key |
| Events / workflow | **EventBridge + Step Functions** | compliance event bus + durable life-events |
| Network isolation | **VPC** (private subnets, Bedrock VPC endpoint) | no public inbound |
| IaC | **CloudFormation** (primary) + **Terraform** (parity) | commercial + GovCloud |

Data-class isolation: separate accounts/VPC boundaries for **CJI, FTI, PHI, education, and general public** data (AWS Organizations / Control Tower) rather than one enterprise boundary. See `COMPLIANCE-CONTROL-MAPPINGS.md`.
