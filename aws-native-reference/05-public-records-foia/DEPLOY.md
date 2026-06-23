# Public Records / FOIA & Redaction — AWS-native deploy (Strands + Step Functions)

Package the 5 Lambdas (`scripts/build_lambdas.sh 05-public-records-foia`), deploy `stepfunctions/05_public_records_foia.asl.json` substituting function ARNs. `HumanGate` uses `waitForTaskToken`. Tests: `python -m pytest tests -q`.
