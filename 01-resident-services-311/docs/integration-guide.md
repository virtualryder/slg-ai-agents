# Agent 01 — Integration Guide

## Systems of record (connector kinds)
| Kind | System examples | Methods | Risk |
|---|---|---|---|
| `crm311` | Salesforce/Cityworks/Accela 311, custom CRM | get/search/create/update | create/update = **write (HITL)** |
| `kb` | Bedrock Knowledge Base, Amazon Q Business, CMS | search_policy, get_article | read |
| `identity` | Cognito / Login.gov / agency IdP | verify_resident | read |
| `consent` | consent ledger | check, record | record = write |
| `scheduling` | Qmatic, Bookings, custom | get_availability, book_appointment | book = **write (HITL)** |
| `gis` | Esri ArcGIS, Amazon Location | get_parcel | read |

## Connector contract
Implement the agency adapter in `platform_core/slg_agent_platform/connectors/live.py`, or
set `<KIND>_BASE_URL` to use the bundled REST adapter (`LiveHttpConnector`). Method
signatures are identical to the fixtures, so **no agent code changes** between demo and live.

## Identity & security trimming
Identity is established at the edge (Cognito federating the agency IdP). The verified
JWT claims (`sub`, `custom:slg_role`) are forwarded to the agent and authorized by the
gateway. A resident must never retrieve, through the agent, anything they could not
retrieve themselves — and personal data requires `identity.verify_resident` to succeed.

## Channels
Web/chat/voice all post the same `/invocations` payload. For voice/contact-center,
Amazon Connect is **optional** — the agent exposes a clean HTTP contract so Connect,
Lex, or any front end can call it without a hard dependency.
