# Deck Sources — grounded figures & citations

*Every number on the agent / WoG / suite decks traces to a source below (re-verified June 2026). Each figure is labeled by evidence tier: **[GOV]** government primary source · **[PEER-REVIEWED]** · **[VENDOR-REPORTED]** (incl. AWS Public Sector Blog and named-government vendor case studies) · **[ANALYST]** (NASCIO, Gartner, Deloitte, NAHB, Euna). Improvement figures are documented results from named deployments applied to a reference agency — not a guarantee. The Honolulu / Clariti CivCheck permitting figure used in the prior version has been **removed** (could not be validated to a primary government source) and replaced with the State of California announcement below.*

---

## Suite-wide proof points
- **NASCIO 2026 State CIO Top-Ten Priorities** — AI is the **#1 priority for 2026**, the first time ever, displacing cybersecurity after 12 years at #1. **[ANALYST]** Dec 2025. https://www.nascio.org/press-releases/theres-a-new-day-in-state-technology-ai-takes-the-top-spot-on-state-cios-priorities-for-2026/
- **NASCIO 2025 State CIO Survey** — **90%** of state CIOs are running GenAI pilots; only **25%** have dedicated GenAI funding (the "pilot trap"). **[ANALYST]** Sep 2025. https://www.nascio.org/resource-center/the-2025-state-cio-survey/
- **Deloitte digital-government survey** — government digital-service satisfaction trails the private sector by **~21 percentage points** (survey of 5,800 across 13 countries; underlying data 2023 — verify exact wording before print). **[ANALYST]** https://www.deloitte.com/us/en/insights/industry/government-public-sector-services/digital-government-survey-insights.html
- **GAO-25-107795** — federal government spends **$100B+/yr on IT, ~80% on operations & maintenance** of existing/legacy systems; 11 critical legacy systems flagged; only 3 of 10 systems flagged in 2019 modernized by 2025. **[GOV]** Jul 17, 2025. https://www.gao.gov/products/gao-25-107795
  - *Note: the older "$337M for 10 legacy systems" figure is from GAO-23-106821, NOT this report. Use the $100B / 80% figures.*

## Compliance / security posture (CISO)
- **Amazon Bedrock FedRAMP High + DoD IL-4/5 in AWS GovCloud (US)** — Bedrock features incl. Agents, **Guardrails, Knowledge Bases**, and Model Evaluation covered; first cloud provider to achieve this for Anthropic Claude and Meta Llama models. **[VENDOR-REPORTED · primary AWS]** May 2025. https://aws.amazon.com/blogs/publicsector/accelerating-government-innovation-amazon-bedrock-models-get-fedramp-high-and-dod-il-4-5-approval-in-aws-govcloud-us/
- **DOJ ADA Title II web rule (WCAG 2.1 AA)** — compliance dates extended one year by the Apr 20, 2026 Interim Final Rule: **Apr 26, 2027** (≥50,000 population) / **Apr 26, 2028** (smaller + special districts). The extension delays the WCAG deadline, **not** liability. **[GOV]** https://www.ada.gov/resources/2024-03-08-web-rule/ · IFR: https://www.federalregister.gov/documents/2026/04/20/2026-07663/extension-of-compliance-dates-for-nondiscrimination-on-the-basis-of-disability-accessibility-of-web

---

## 01 Resident Services / 311
- **Gartner** — live-agent contact **$8.01** vs. **~$0.10** self-service (~80×); only **9%** of customers fully self-resolve. **[ANALYST]** Sep 25, 2019 (cross-industry, cite precisely as $8.01). https://www.gartner.com/en/newsroom/press-releases/2019-09-25-gartner-says-only-9--of-customers-report-solving-thei
- **NYC Office of Technology & Innovation** — NYC311 handles **98,028 contacts/day**; 525M+ lifetime. **[GOV]** 2023. https://www.nyc.gov/assets/oti/downloads/pdf/reports/311-Report-2023.pdf
- **Brynjolfsson, Li & Raymond, "Generative AI at Work"** — gen-AI support copilot **+14%** issues/hr avg, **+34%** for novices. Cite the **peer-reviewed** version: *Quarterly Journal of Economics* 140(2), 2025, pp. 889–942 (NBER w31161 is the working paper). **[PEER-REVIEWED]** https://www.nber.org/papers/w31161
- **Results — North Carolina DES** assistant: **2,700 inquiries** in month one, on AWS GovCloud. **[VENDOR-REPORTED]** May 30, 2025. https://aws.amazon.com/blogs/publicsector/north-carolina-division-of-employment-security-modernizes-customer-services-with-generative-ai-on-aws/
- **Results — Denver "Sunny" (Citibot on AWS)**: handled **~20% of all 311 interactions** (95,000 conversations), **85%** approval, **45%** peak-season live-agent staffing reduction. **[VENDOR-REPORTED]** Jan 7, 2026. https://www.civicmarketplace.com/news/city-and-county-of-denver-improve-311-performance-with-ai-powered-virtual-assistant
  - *Kept off-slide: Virginia Beach "1,300+ queries month one" is a usage figure, not proven deflection.*

## 02 Forms & IDP
- **Anne Arundel County, MD ("GIST" on AWS)** — manual intake **~45 min → <20s** voicemail summarization; hour-long manual steps now "almost no manual effort"; built on **Bedrock + Textract + Transcribe + Guardrails + human-in-the-loop** (named CIO Jack Martin). Permitting = **>30% of county web traffic**. **[VENDOR-REPORTED · named gov]** Feb 23, 2026. https://aws.amazon.com/blogs/publicsector/anne-arundel-county-integrates-generative-ai-into-case-management-to-empower-staff-and-improve-citizen-services/
- **Mays & Mathias, JAMIA (2019)** — manual transcription error **~3.7%**; literature benchmarks incl. **~1.01% double-key / 2.02% single-key** entry. **[PEER-REVIEWED]** https://academic.oup.com/jamia/article/26/3/269/5287977
- **AWS Public Sector Blog** — government IDP reference pattern (Textract + Comprehend + A2I); applications can "languish for weeks or months." **[VENDOR-REPORTED · architecture]** Jan 28, 2025. https://aws.amazon.com/blogs/publicsector/transforming-government-application-systems-using-intelligent-document-processing-on-aws/

## 03 Permitting & Licensing  *(replaces Honolulu)*
- **Office of the Governor of California (Newsom)** — AI-powered **e-check plan review** (Archistar) provided to LA City & County; brings permitting from **"weeks and months" to "hours or days"** (Steadfast LA Chair Rick Caruso); uses computer vision + ML + automated rulesets to check designs against local codes pre-submission; **contributions from Autodesk and Amazon**; already used by **25+ municipalities** (Austin, Houston, Seattle, Colorado…); now on a **statewide contract**. **[GOV]** Apr 30, 2025. https://www.gov.ca.gov/2025/04/30/governor-newsom-announces-launch-of-new-ai-tool-to-supercharge-the-approval-of-building-permits-and-speed-recovery-from-los-angeles-fires/
- **City of Austin** — reports **~50% zoning-review time savings** with AI pre-check (Archistar); 5-year contract after a 3-month pilot. The 50% is **vendor (Archistar)** but carries a named City of Austin official's attribution; present as "the City of Austin reports ~50%." **[VENDOR-REPORTED · named gov]** Cities Today, Oct 16, 2024. https://cities-today.com/austin-launches-ai-driven-building-permit-software/
- **NAHB, Government Regulation in the Price of a New Home (2025)** — regulation = **>26%** of a new single-family home's price; **94.2%** of developers say regulations cause project delays. **[ANALYST]** Feb 2025. https://www.nahb.org/news-and-economics/press-releases/2025/02/home-builders-tell-congress-how-permitting-roadblocks-raise-housing-costs
  - *On-slide honesty: do not claim a fixed % cut to end-to-end issuance; the credible story is fewer correction cycles and faster valid submissions.*

## 04 Benefits / HHS
- **USDA FNS** — SNAP **FY2024 national payment error rate 10.93%**; 44 states required to file corrective action plans (threshold 6%). **[GOV]** Jun 27, 2025. https://www.fns.usda.gov/newsroom/fns-0003.25
- **KFF** — **69%** of Medicaid "unwinding" disenrollments were procedural (data as of Sept 12, 2024). **[ANALYST]** https://www.kff.org/medicaid/medicaid-enrollment-and-unwinding-tracker/
- **Results — Nevada DETR (Google Vertex AI)** — unemployment-appeal ruling drafted in **~5 minutes vs. hours** (frame as "minutes instead of hours"); backlog of **over 10,000** appeals targeted by AI triage. **[NAMED GOV · tech press]** Sep 11, 2024. https://www.engadget.com/ai/nevada-will-use-google-ai-to-process-a-backlog-of-unemployment-cases-202718427.html
  - *Corrections vs. prior version: do NOT use "40,000 → 5,000" (unverified); UNLV is an independent critic, not a pilot partner.*
- **Results — Georgia DOL "George"** — **993,141 sessions**, **97%** routed accurately, 64,000+ users. **[VENDOR/STATE-REPORTED]** Feb 7, 2023. https://statescoop.com/georgia-labor-upgrades-ai-chatbot/

## 05 Public Records / FOIA
- **DOJ Office of Information Policy, FY2024 Summary of Annual FOIA Reports** — government-wide **backlog 267,056 (+33%)**; **1,501,432 requests received (+25%)**; total cost **$723,415,561 ($723.4M)**; simple-track average **44 days**. **[GOV]** Apr 28, 2025. https://www.justice.gov/oip/blog/summary-fiscal-year-2024-annual-foia-reports-published
- **Results — Kofile "Kleio" on AWS** — county records search **"hours → seconds"**, serving **3,000+ counties**. **[VENDOR-REPORTED]** May 5, 2026. https://aws.amazon.com/blogs/publicsector/how-kofile-modernizes-county-records-with-ai-on-aws/
- **Results — CaseGuard** — automates redactions **85% faster** (vendor marketing claim). **[VENDOR-REPORTED]** https://caseguard.com/use-cases/law-enforcement/

## 06 Procurement & Grants
- **Euna Solutions** — average public-sector RFP cycle **57 days** posting-to-award (6,000+ RFPs); **~90 hours** staff effort per RFP (2024 NCPP data); most agencies see only **2–5 bids**. **[ANALYST/VENDOR]** *(57-day figure originally ~2019, page refreshed 2026 — pair with the 90-hour 2024 number).* https://eunasolutions.com/resources/2025-state-of-public-procurement/
- **GAO-24-106528** — median acquisition lead time (PALT) on DoD contracts **>$50M rose ~70 days** FY2019–22 (federal/DoD; frame as "acquisition lead times are long and growing"). **[GOV]** https://www.gao.gov/products/gao-24-106528
- **Results — Inventive.ai** — AI drafting assistant reduced RFP creation time **~70%** at an **unnamed** state DOT (vendor blog; no named government deployment verified — present honestly). **[VENDOR-REPORTED · unnamed agency]** https://www.inventive.ai/blog-posts/ai-government-rfp-workflow-tips

## 07 GovOps IT Service Desk
- **IBM AskIT (watsonx Assistant)** — **75%** of IT queries self-resolved by the assistant; 133,000+ users, trained on ~300,000 tickets. **[VENDOR-REPORTED]** https://www.ibm.com/case-studies/cio-watsonx-askit
- **ServiceNow ITSM AI/ML (Microsoft internal Global Helpdesk)** — MTTR reduced **>10%**; incident routing 80% accurate. *This is Predictive Intelligence (ML), NOT "Now Assist" — do not attribute to Now Assist.* **[VENDOR-REPORTED]** https://www.microsoft.com/insidetrack/blog/modernizing-the-support-experience-with-servicenow-and-microsoft/
- **Brynjolfsson et al. (QJE 2025)** — **+14% / +34%** productivity (see 01). **[PEER-REVIEWED]**
- **GAO-25-107795** — $100B+/yr, ~80% O&M, legacy-system risk (see suite-wide). **[GOV]**

## 08 Public Safety / Public Health
- **CDC TowerScout** — cooling-tower identification **4 hours → 5 minutes (−98%)**; used in **12+ outbreak investigations across 8 states** since 2021. **[GOV]** Sep 12, 2025. https://www.cdc.gov/public-health-data-strategy/php/story/using-ai-to-improve-public-health-efficiency.html
  - *Honesty note (in speaker notes): the 98% / 4-hr→5-min figure is footnoted by CDC as based on "unpublished CDC studies." The peer-reviewed paper validates detection accuracy, not the time savings — keep the two claims distinct.*
- **The Lancet Digital Health (2024)** — peer-reviewed model development & validation study behind TowerScout. **[PEER-REVIEWED]** https://www.thelancet.com/journals/landig/article/PIIS2589-7500(24)00094-3/fulltext
- **Axon Draft One** — officers spend up to **40%** of time on reports; Leon County **24.6 → 9.46 min (−61%)** in a 90-day trial. **[VENDOR-REPORTED]** https://www.axon.com/blog/reducing-time-spent-on-report-writing-for-officers
- **Counter-evidence (moved to speaker notes per design):**
  - Pre-registered **RCT** found AI did **not** significantly speed report writing (n=85 officers, 755 reports; 6,084-report robustness check). *J. Experimental Criminology* 2024. **[PEER-REVIEWED]** https://link.springer.com/article/10.1007/s11292-024-09644-7
  - **Anchorage PD** ran a 90-day Draft One trial and declined to keep it. EFF, Mar 2025. https://www.eff.org/deeplinks/2025/03/anchorage-police-department-ai-generated-police-reports-dont-save-time

## WoG Platform & Suite
- NASCIO 2025–2026, GAO-25-107795, Deloitte, Bedrock FedRAMP High/IL-4-5, ADA Title II — see suite-wide / compliance sections above.

---

### Labeling discipline for slides
- The only **[GOV] + [PEER-REVIEWED]** anchor is **CDC TowerScout** — lead public-safety with it.
- **[GOV]** figures (cite as-is): SNAP 10.93%; all four DOJ FOIA numbers; California permitting; GAO IT/PALT; CDC TowerScout; ADA dates.
- **Vendor-reported** outcomes (NC DES, Denver, Anne Arundel, Kofile, CaseGuard, IBM, ServiceNow, Inventive, Austin) are tagged **VENDOR-REPORTED** on-slide; named-government ones add "· NAMED GOV."
- Counter-evidence and caveats live in **speaker notes**, not on slides (per design choice) — but presenters should volunteer them when asked.
