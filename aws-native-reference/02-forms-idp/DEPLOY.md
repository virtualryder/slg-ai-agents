# Forms & Intelligent Document Processing — AWS-native deploy (Strands + Step Functions)

Package the 5 Lambdas with platform_core + governance as a layer (`scripts/build_lambdas.sh 02-forms-idp`), deploy `stepfunctions/02_forms_idp.asl.json` substituting the function ARNs. `HumanGate` uses `waitForTaskToken`. Run tests: `python -m pytest tests -q`.
