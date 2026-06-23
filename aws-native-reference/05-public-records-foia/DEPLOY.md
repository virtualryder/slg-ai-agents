# Public Records / FOIA & Redaction — AWS-native deploy (Strands + Step Functions)

Package the 5 Lambdas with platform_core + governance as a layer (`scripts/build_lambdas.sh 05-public-records-foia`), deploy `stepfunctions/05_public_records_foia.asl.json` substituting the function ARNs. `HumanGate` uses `waitForTaskToken`. Run tests: `python -m pytest tests -q`.
