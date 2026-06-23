# Forms & Intelligent Document Processing — AWS-native deploy (Strands + Step Functions)

Package the 5 Lambdas (`scripts/build_lambdas.sh 02-forms-idp`), deploy `stepfunctions/02_forms_idp.asl.json` substituting function ARNs. `HumanGate` uses `waitForTaskToken`. Tests: `python -m pytest tests -q`.
