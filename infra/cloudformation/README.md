# CloudFormation Quick Deploy

One master template (`quickstart.yaml`) provisions a customer-isolated SLG agent environment.

| Template | Purpose |
|---|---|
| `quickstart.yaml` | Master — nests the stacks; `GatewayMode` + `DeployMode` switch variants |
| `security.yaml` | KMS CMK, Bedrock Guardrail (PII/denied-topics), Cognito pool+client, least-privilege agent role |
| `data.yaml` | Append-only DynamoDB audit (PITR), **S3 Object Lock COMPLIANCE (WORM, 7-yr)**, HITL table |
| `gateway-portable.yaml` | MCP layer **Path A** — API Gateway HTTP API + Cognito JWT authorizer (**any region, incl. GovCloud**) |
| `agentcore-gateway.yaml` | MCP layer **Path B** — Bedrock AgentCore Gateway + Identity (AgentCore regions) |
| `agent-service.yaml` | The agent — native (Step Functions + Lambda + `waitForTaskToken` HITL) or container (ECS Fargate / AgentCore Runtime) |

```bash
aws cloudformation deploy --template-file quickstart.yaml \
  --stack-name slg-01-resident-services-dev \
  --parameter-overrides AgentId=01-resident-services-311 Environment=dev \
                        GatewayMode=portable DeployMode=native \
                        TemplateBaseUrl=https://my-cfn-bucket.s3.amazonaws.com/slg \
  --capabilities CAPABILITY_NAMED_IAM
```

> **GovCloud:** use `GatewayMode=portable`. As of 2026-05 AgentCore Gateway semantic
> search / Memory / Policy / Registry are not in GovCloud; Bedrock + Guardrails +
> Knowledge Bases are FedRAMP High / IL-4/5 approved. See `../../docs/COMPLIANCE-CONTROL-MAPPINGS.md`.
