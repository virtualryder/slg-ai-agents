# GovOps IT Service Desk & Modernization — AWS-native deploy (Strands + Step Functions)

Package the 5 Lambdas (`scripts/build_lambdas.sh 07-govops-service-desk`), deploy `stepfunctions/07_govops_service_desk.asl.json` substituting function ARNs. `HumanGate` uses `waitForTaskToken`. Tests: `python -m pytest tests -q`.
