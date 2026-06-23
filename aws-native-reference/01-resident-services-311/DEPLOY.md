# Agent 01 — AWS-native deploy (Strands + Step Functions)

1. **Package** the 5 Lambdas (`classify`, `draft`, `check`, `hitl_notify`, `finalize`) with `platform_core` + `governance` as a layer: `scripts/build_lambdas.sh 01-resident-services-311`.
2. **Deploy** the state machine from `stepfunctions/resident_services.asl.json`, substituting the function ARNs (`${ClassifyFn}` …). The `HumanGate` state uses `waitForTaskToken` — your reviewer UI calls `SendTaskSuccess` with the approval payload to resume.
3. **Drafting** (`draft`) runs Strands + Bedrock (Claude) wrapped by a Bedrock Guardrail; in GovCloud use the portable gateway path (AgentCore Gateway semantic search is not yet in GovCloud).
4. **Audit:** every Lambda emits to the append-only DynamoDB audit table; finalized snapshots to S3 Object Lock.

Run the native tests: `python -m pytest tests -q` (no AWS account needed).
