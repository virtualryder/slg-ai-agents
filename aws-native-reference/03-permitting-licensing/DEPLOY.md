# Permitting & Licensing — AWS-native deploy (Strands + Step Functions)

Package the 5 Lambdas (`scripts/build_lambdas.sh 03-permitting-licensing`), deploy `stepfunctions/03_permitting_licensing.asl.json` substituting function ARNs. `HumanGate` uses `waitForTaskToken`. Tests: `python -m pytest tests -q`.
