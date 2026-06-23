# Why the MCP Authorization Layer — and why fund it in Phase 1

**Plain English:** An agent that only *answers questions* needs good content. An agent that *does things in government systems* — opens a case, books an appointment, drafts a notice, routes a permit — needs a governed front door, or you have built an unaccountable robot with a service account.

The MCP authorization gateway is that front door. Every tool call passes one enforcement point that:
1. **Authenticates** the acting public servant (verified IdP claims; fail-closed).
2. **Authorizes** deny-by-default with least-privilege intersection — *the agent can never do more than the human on whose behalf it acts.*
3. **Gates** high-risk writes behind a verified human approval record.
4. **Mints** a short-lived token scoped to exactly one tool — no standing service accounts.
5. **Audits** every attempt, PII/CJI/FTI-masked, with lineage to the system reached.

**Talk track for a CISO:** "Show me who did what, on whose authority, to which record, and prove the agent couldn't exceed the employee." This layer is that proof. **For a CIO:** it is the difference between one auditable platform and dozens of ungoverned point integrations you re-explain at every audit. **Objection — 'MCP handles auth, right?'** No. MCP standardizes *tool discovery and invocation*; it does not provide authorization, policy enforcement, or audit. Those are the gateway's job (AgentCore Gateway + Identity, or API Gateway + Lambda authorizer + STS + Cedar/OPA).

Fund it in Phase 1 because retrofitting authorization and audit onto live agents that already touch constituent data is the most expensive way to discover you needed it.
