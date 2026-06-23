# Benefits / HHS Caseworker Assist — AWS-native deploy (Strands + Step Functions)

Package the 5 Lambdas with platform_core + governance as a layer (`scripts/build_lambdas.sh 04-benefits-caseworker`), deploy `stepfunctions/04_benefits_caseworker.asl.json` substituting the function ARNs. `HumanGate` uses `waitForTaskToken`. Run tests: `python -m pytest tests -q`.
