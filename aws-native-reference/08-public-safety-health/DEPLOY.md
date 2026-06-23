# Public Safety / Public Health Case & Report — AWS-native deploy (Strands + Step Functions)

Package the 5 Lambdas with platform_core + governance as a layer (`scripts/build_lambdas.sh 08-public-safety-health`), deploy `stepfunctions/08_public_safety_health.asl.json` substituting the function ARNs. `HumanGate` uses `waitForTaskToken`. Run tests: `python -m pytest tests -q`.
