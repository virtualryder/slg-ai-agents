# Public Safety / Public Health Case & Report — AWS-native deploy (Strands + Step Functions)

Package the 5 Lambdas (`scripts/build_lambdas.sh 08-public-safety-health`), deploy `stepfunctions/08_public_safety_health.asl.json` substituting function ARNs. `HumanGate` uses `waitForTaskToken`. Tests: `python -m pytest tests -q`.
