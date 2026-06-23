# AWS-native shared building blocks
- `runtime/` — the ARM64 container contract (`/invocations` + `/ping`) for AgentCore Runtime / ECS Fargate, shared by all container-mode agents.
- `connector/` — the governed connector Lambda handler invoked by the gateway; one deployment per system of record, deny-by-default upstream.
