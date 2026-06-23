# Sources & Grounding
*All architecture, compliance, and market claims in this repository trace to the sources below. Verified June 2026. Where a claim could not be confirmed against a primary source it is omitted rather than asserted.*

## AWS platform
- **Amazon Bedrock AgentCore — GA (Oct 13, 2025)**; components: Runtime, Memory, Gateway, Identity, Code Interpreter, Browser, Observability. https://aws.amazon.com/about-aws/whats-new/2025/10/amazon-bedrock-agentcore-available/ · https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/what-is-bedrock-agentcore.html
- **AgentCore Gateway** (APIs/Lambdas/MCP → governed tools) & **Identity** (scoped, delegated tokens; Cognito/Okta/Entra/Auth0). https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/gateway.html · https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/identity.html
- **GovCloud:** Bedrock + Agents + Guardrails + Knowledge Bases are FedRAMP High / DoD IL-4/5 approved (May 23, 2025). https://aws.amazon.com/about-aws/whats-new/2025/05/amazon-bedrock-models-fedramp-high-dod-il-4-5-govcloud/ · AgentCore launched in GovCloud (US-West) May 5, 2026 — Memory, Gateway semantic search, Policy, Registry **not** yet included. https://aws.amazon.com/about-aws/whats-new/2026/05/bedrock-agentcore-launch-aws-govcloud-us/ · https://docs.aws.amazon.com/govcloud-us/latest/UserGuide/govcloud-bedrock-agentcore.html
- **Strands Agents SDK 1.0 GA (Jul 15, 2025)** — open-source, model-driven multi-agent SDK. https://aws.amazon.com/blogs/opensource/introducing-strands-agents-1-0-production-ready-multi-agent-orchestration-made-simple/ · https://strandsagents.com/
- **AWS public-sector agentic AI (Jun 8, 2026)** — partner citizen-services/forms agents on AgentCore + Strands. https://aws.amazon.com/blogs/publicsector/production-ready-in-months-aws-partners-deliver-agentic-ai-solutions-for-public-sector/
- **Bedrock Guardrails** — PII filters, denied topics, contextual grounding checks. https://docs.aws.amazon.com/bedrock/latest/userguide/guardrails.html
- **Bedrock Knowledge Bases** (OpenSearch Serverless / Aurora pgvector) & **Amazon Q Business**. https://docs.aws.amazon.com/bedrock/latest/userguide/knowledge-base-setup.html · https://docs.aws.amazon.com/amazonq/latest/qbusiness-ug/what-is.html

## SLG market & deployments
- **NASCIO 2026 — AI is the #1 state CIO priority** (cyber drops to #2); 2025 survey: 90% running GenAI pilots, 25% have dedicated GenAI funding. https://www.nascio.org/press-releases/theres-a-new-day-in-state-technology-ai-takes-the-top-spot-on-state-cios-priorities-for-2026/ · https://statescoop.com/nascio-2025-annual-survey/
- **Virginia Beach** AI search assistant — 1,300+ queries in month one (Kendra + Bedrock + Guardrails). https://aws.amazon.com/blogs/publicsector/city-of-virginia-beach-launches-ai-powered-search-assistant-to-transform-citizen-access-to-information/
- **Anne Arundel County "GIST"** — 45+ min → under 20s case summarization (Bedrock + Transcribe + Textract, HITL). https://aws.amazon.com/blogs/publicsector/anne-arundel-county-integrates-generative-ai-into-case-management-to-empower-staff-and-improve-citizen-services/
- **North Carolina DES "SCUBI"** — public UI assistant, 2,700 inquiries month one, on **AWS GovCloud**, mapped to NIST AI RMF. https://aws.amazon.com/blogs/publicsector/north-carolina-division-of-employment-security-modernizes-customer-services-with-generative-ai-on-aws/
- **Kofile "Kleio"** — Bedrock document intelligence across 3,000+ county governments. https://aws.amazon.com/blogs/publicsector/how-kofile-modernizes-county-records-with-ai-on-aws/

## Compliance
- **GovRAMP (formerly StateRAMP, rebranded Feb 14, 2025)** — AWS GovCloud High / US East-West Moderate. https://aws.amazon.com/compliance/govramp/ · https://govramp.org/product-list/
- **FBI CJIS Security Policy v6.0** (eff. Dec 27, 2024). https://www.fbi.gov/file-repository/cjis
- **IRS Publication 1075** (Rev. 11-2021, eff. Jun 10, 2022) — FTI safeguards (NIST 800-53 Rev 5). https://www.irs.gov/pub/irs-pdf/p1075.pdf
- **ADA Title II web rule** — WCAG 2.1 AA; **DOJ Apr 2026 IFR extended deadlines one year**: ≥50k pop. **Apr 26, 2027**; smaller/special districts **Apr 26, 2028**. https://www.ada.gov/resources/2024-03-08-web-rule/ · https://www.federalregister.gov/documents/2026/04/20/2026-07663/extension-of-compliance-dates-for-nondiscrimination-on-the-basis-of-disability-accessibility-of-web
- **NIST AI RMF 1.0** (Jan 26, 2023) — Govern/Map/Measure/Manage. https://www.nist.gov/itl/ai-risk-management-framework
- **HIPAA + CMS MARS-E v2.2 → ARC-AMPE** (successor, Mar 4, 2026 implementation). https://www.cms.gov/files/document/mars-e-v2-2-vol-1final-signed08032021-1.pdf · **FERPA** (34 CFR Part 99). https://studentprivacy.ed.gov/faq/what-ferpa · **DPPA** (18 U.S.C. 2721). https://www.law.cornell.edu/uscode/text/18/2721
