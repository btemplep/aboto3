
import os
from typing import Any

import boto3
from moto import mock_ssm
import pytest

from aboto3 import AIOClient


@pytest.fixture(scope="function")
def moto_creds() -> None:
    cred_env_vars = [
        "AWS_ACCESS_KEY_ID",
        "AWS_SECRET_ACCESS_KEY",
        "AWS_SECURITY_TOKEN",
        "AWS_SESSION_TOKEN"
    ]
    aws_creds = {}
    for env_var in cred_env_vars:
        aws_creds[env_var] = os.environ.get(env_var, None)
        os.environ[env_var] = "testing"

    yield

    for cred in aws_creds:
        if aws_creds[cred] is None:
            os.environ.pop(cred)
        else:
            os.environ[cred] = aws_creds[cred]


@pytest.fixture
def param_key() -> str:
    return "/my/param/key"

@pytest.fixture
def param_value() -> str:
    return "my param value"


@pytest.fixture(scope="function")
def ssm_client(moto_creds: None) -> Any:
    with mock_ssm():
        yield boto3.client("ssm", region_name="us-east-1")


@pytest.fixture(scope="function")
def aio_ssm_client(ssm_client) -> AIOClient:
    return AIOClient(boto3_client=ssm_client)


@pytest.fixture(scope="function")
def add_param(
    ssm_client: Any,
    param_key: str,
    param_value: str
) -> None:
    ssm_client.put_parameter(
        Name=param_key,
        Value=param_value,
        Type="String"
    )
