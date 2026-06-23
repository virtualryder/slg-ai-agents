# Deck Sources — grounded figures & citations
*Every number on the agent/WoG decks traces to a source below (verified June 2026). Improvement figures are documented results applied to a reference agency, not a guarantee. Vendor-reported figures are flagged.*

## Suite-wide proof points (AWS Public Sector Blog)
- **Virginia Beach** AI search assistant — 1,300+ queries in month one. https://aws.amazon.com/blogs/publicsector/city-of-virginia-beach-launches-ai-powered-search-assistant-to-transform-citizen-access-to-information/
- **Anne Arundel County (MD)** — manual intake ~45 min → under 20 seconds (Bedrock + Textract + Transcribe). https://aws.amazon.com/blogs/publicsector/anne-arundel-county-integrates-generative-ai-into-case-management-to-empower-staff-and-improve-citizen-services/ (Feb 23, 2026)
- **North Carolina DES** unemployment assistant — 2,700 inquiries in month one, on AWS GovCloud. https://aws.amazon.com/blogs/publicsector/north-carolina-division-of-employment-security-modernizes-customer-services-with-generative-ai-on-aws/ (May 30, 2025)
- **Kofile** — county records search "hours → seconds," 3,000+ counties, on Bedrock. https://aws.amazon.com/blogs/publicsector/how-kofile-modernizes-county-records-with-ai-on-aws/ (May 5, 2026)
- **Grupo TX "TxGov"** — 35% call-volume reduction, 50% faster response (48h→24h), 92% CSAT. https://aws.amazon.com/blogs/publicsector/production-ready-in-months-aws-partners-deliver-agentic-ai-solutions-for-public-sector/ (Jun 8, 2026)

## 01 Resident Services / 07 GovOps service desk
- **Gartner (Sep 25, 2019):** live contact ≈ $8.01 vs ≈ $0.10 self-service; only 9% of customers fully self-resolve. https://www.gartner.com/en/newsroom/press-releases/2019-09-25-gartner-says-only-9--of-customers-report-solving-thei
- **NBER w31161 (Brynjolfsson, Li & Raymond, 2023):** genAI support copilot +14% productivity avg, +34% for novice agents. https://www.nber.org/papers/w31161

## 02 Forms & IDP
- **Anne Arundel County** (45 min → <20s) — AWS, above. **Arizona** Textract benefits portal auto-approved 49% of applications — https://aws.amazon.com/blogs/publicsector/using-ai-rethink-document-automation-extract-insights/
- Manual data-entry error rate 1–4% of fields — industry aggregation (Lido). https://www.lido.app/blog/data-entry-error-rates

## 03 Permitting & Licensing
- **Permit Place 2026 Permit Speed Index:** US avg first commercial plan review 19.2 business days. https://permitplace.com/permit-speed-index/
- **Honolulu DPP + Clariti CivCheck (vendor-reported):** days-to-decision 73 → 32.5 (−55%); residential review −70%; corrections −67%. https://www.claritisoftware.com/honolulu-cuts-review-times-by-70-percent-with-civchecks-ai-plan-review-software
- **Soltas & Gruber (2026), "How Costly Is Permitting in Housing Development?":** permitting ≈ one-third of the price-vs-cost gap; +50% for ready-to-issue land. https://evansoltas.com/papers/Permitting_SoltasGruber2026.pdf

## 04 Benefits / HHS
- **KFF (2024):** 69% of Medicaid "unwinding" disenrollments were procedural. https://www.kff.org/medicaid/medicaid-enrollment-and-unwinding-tracker/
- **USDA FNS (Jun 27, 2025):** SNAP FY2024 payment error rate 10.93%. https://www.fns.usda.gov/newsroom/fns-0003.25
- **CMS via PBS (2023):** benefits call centers avg 25-min wait, 29% abandonment. https://www.pbs.org/newshour/politics/federal-officials-raise-concerns-about-long-call-center-wait-times-as-millions-are-dropped-from-medicaid

## 05 Public Records / FOIA
- **DOJ OIP 2024 Annual FOIA Report Summary (Apr 28, 2025):** backlog 267,056 (+33%); 1,501,432 requests received (+25%); $723.4M government-wide cost; simple-request avg 44 days. https://www.justice.gov/oip/media/1398111/dl?inline=
- **Kofile** (hours → seconds, 3,000+ counties) — AWS, above.

## 06 Procurement & Grants
- **Euna/Bonfire (6,000+ public-sector RFPs):** average cycle 57 days posting to award. https://eunasolutions.com/resources/your-guide-to-rfp-cycle-times-in-public-procurement/
- **GAO-24-106528:** DoD acquisition lead time (PALT) for contracts >$50M rose ~70 days FY2019–22. https://www.gao.gov/products/gao-24-106528
- **Inventive.ai (vendor, 2025):** RFP completion 30 → 25 hrs (−17%) with AI drafting. https://www.inventive.ai/blog-posts/ai-government-rfp-workflow-tips

## 08 Public Safety / Public Health
- **Axon (Apr 16, 2025):** officers spend up to 40% of time on report-writing; Draft One "cuts report time in half" (Leon County 24.6 → 9.46 min, −61%). https://www.axon.com/blog/reducing-time-spent-on-report-writing-for-officers
- **Counter-evidence (presented for credibility):** EFF (Mar 12, 2025) — Anchorage PD found no significant time savings; pre-registered RCT (J. Exp. Criminology, 2024) found AI did not significantly improve report-writing speed. https://www.eff.org/deeplinks/2025/03/anchorage-police-department-ai-generated-police-reports-dont-save-time · https://link.springer.com/article/10.1007/s11292-024-09644-7
- **CDC (Sep 12, 2025):** TowerScout cut cooling-tower identification 98% (4 hrs → 5 min). https://www.cdc.gov/public-health-data-strategy/php/story/using-ai-to-improve-public-health-efficiency.html

## WoG Platform
- **NASCIO 2026 priorities & 2025 survey:** AI = #1 state-CIO priority; 90% piloting GenAI, 25% with dedicated funding. https://www.nascio.org/press-releases/theres-a-new-day-in-state-technology-ai-takes-the-top-spot-on-state-cios-priorities-for-2026/
- **DOJ ADA Title II 2026 Interim Final Rule:** compliance deadlines extended to Apr 26 2027 (≥50k pop.) / Apr 26 2028 (smaller + special districts). https://www.federalregister.gov/documents/2026/04/20/2026-07663/extension-of-compliance-dates-for-nondiscrimination-on-the-basis-of-disability-accessibility-of-web
