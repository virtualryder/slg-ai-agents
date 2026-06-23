# Procurement, Contracting & Grants — AWS-native deploy (Strands + Step Functions)

Package the 5 Lambdas (`scripts/build_lambdas.sh 06-procurement-grants`), deploy `stepfunctions/06_procurement_grants.asl.json` substituting function ARNs. `HumanGate` uses `waitForTaskToken`. Tests: `python -m pytest tests -q`.
