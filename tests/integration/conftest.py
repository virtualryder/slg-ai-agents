"""Integration fixtures — run ONLY against a deployed golden-path stack (P9).

These tests authenticate to the deployed Cognito user pool, call the live HTTP API, and read
the live DynamoDB audit/pending tables + Step Functions. They are skipped entirely unless
`SLG_STACK` is set (so the offline unit suite never tries to reach AWS). CI deploys an
ephemeral stack, sets SLG_STACK, runs these, then tears the stack down.

Required env: SLG_STACK (CloudFormation stack name). Optional: AWS_REGION (default us-east-1).
Requires AWS credentials with cloudformation:Describe*, cognito-idp admin*, dynamodb, states.
"""
import os
import secrets
import string

import pytest

STACK = os.getenv("SLG_STACK")
REGION = os.getenv("AWS_REGION", "us-east-1")

pytestmark = pytest.mark.integration

if not STACK:
    pytest.skip("integration tests require a deployed stack (set SLG_STACK)", allow_module_level=True)

boto3 = pytest.importorskip("boto3")


def _strong_password() -> str:
    pools = [string.ascii_uppercase, string.ascii_lowercase, string.digits, "!@#$%^&*"]
    base = [secrets.choice(p) for p in pools]
    base += [secrets.choice("".join(pools)) for _ in range(12)]
    secrets.SystemRandom().shuffle(base)
    return "".join(base)


@pytest.fixture(scope="session")
def outputs():
    cf = boto3.client("cloudformation", region_name=REGION)
    st = cf.describe_stacks(StackName=STACK)["Stacks"][0]
    return {o["OutputKey"]: o["OutputValue"] for o in st.get("Outputs", [])}


@pytest.fixture(scope="session")
def cognito(outputs):
    """Provision two users (a requestor + a reviewer) and return their ID tokens.

    Both hold RESIDENT_SERVICES_AGENT (the role entitled to the 311 write) — the reviewer is a
    DIFFERENT subject, so separation of duties is satisfied by identity, not by role.
    """
    from pycognito import Cognito  # CI installs pycognito for SRP auth
    idp = boto3.client("cognito-idp", region_name=REGION)
    pool = outputs["UserPoolId"]
    # client id: the API's JWT authorizer trusts this exact client (aud == client_id on the ID token)
    client = next(c["ClientId"] for c in
                  idp.list_user_pool_clients(UserPoolId=pool, MaxResults=10)["UserPoolClients"])

    def mk(username, role):
        pw = _strong_password()
        idp.admin_create_user(UserPoolId=pool, Username=username, MessageAction="SUPPRESS",
                              UserAttributes=[{"Name": "custom:slg_role", "Value": role}])
        idp.admin_set_user_password(UserPoolId=pool, Username=username, Password=pw, Permanent=True)
        u = Cognito(pool, client, username=username)
        u.authenticate(password=pw)
        return u.id_token

    suffix = secrets.token_hex(3)
    return {
        "requestor": mk(f"it-req-{suffix}", "RESIDENT_SERVICES_AGENT"),
        "reviewer": mk(f"it-rev-{suffix}", "RESIDENT_SERVICES_AGENT"),
        "base_url": outputs["GatewayUrl"],
    }
