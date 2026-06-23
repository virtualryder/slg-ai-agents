# Permitting & Licensing — AWS-native deploy (Strands + Step Functions)

Package the 5 Lambdas with platform_core + governance as a layer (`scripts/build_lambdas.sh 03-permitting-licensing`), deploy `stepfunctions/03_permitting_licensing.asl.json` substituting the function ARNs. `HumanGate` uses `waitForTaskToken`. Run tests: `python -m pytest tests -q`.
