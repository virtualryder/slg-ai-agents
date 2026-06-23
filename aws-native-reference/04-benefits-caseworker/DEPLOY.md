# Benefits / HHS Caseworker Assist — AWS-native deploy (Strands + Step Functions)

Package the 5 Lambdas (`scripts/build_lambdas.sh 04-benefits-caseworker`), deploy `stepfunctions/04_benefits_caseworker.asl.json` substituting function ARNs. `HumanGate` uses `waitForTaskToken`. Tests: `python -m pytest tests -q`.
