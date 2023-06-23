
import asyncio
from concurrent.futures import ThreadPoolExecutor

import pytest

from aboto3 import AIOClient



def test_aio_client_init(ssm_client) -> None:
    aio_ssm_client = AIOClient(ssm_client)
    assert aio_ssm_client.client == ssm_client
    assert ssm_client._client_config.max_pool_connections == aio_ssm_client._thread_pool._max_workers


def test_aio_client_init_custom_threadpool(ssm_client) -> None:
    thread_pool = ThreadPoolExecutor(max_workers=5)
    aio_ssm_client = AIOClient(
        boto3_client=ssm_client,
        thread_pool_executor=thread_pool
    )
    assert aio_ssm_client.client == ssm_client
    assert aio_ssm_client._thread_pool._max_workers == 5
    assert ssm_client._client_config.max_pool_connections != aio_ssm_client._thread_pool._max_workers


def test_bad_method_name(aio_ssm_client: AIOClient) -> None:
    with pytest.raises(AttributeError):
        aio_ssm_client.unknown_method()


def test_describe_params_empty(aio_ssm_client: AIOClient) -> None:
    resp = aio_ssm_client.client.describe_parameters()
    async_resp = asyncio.run(aio_ssm_client.describe_parameters())
    assert "Parameters" in resp
    assert "Parameters" in async_resp
    assert len(resp['Parameters']) == 0
    assert len(async_resp['Parameters']) == 0


@pytest.mark.asyncio
async def test_put_param(
    aio_ssm_client: AIOClient,
    param_key: str,
    param_value: str
) -> None:
    await aio_ssm_client.put_parameter(
        Name=param_key,
        Value=param_value,
        Type="String"
    )
    resp = aio_ssm_client.client.get_parameter(Name=param_key)
    async_resp = await aio_ssm_client.get_parameter(Name=param_key)
    assert resp['Parameter'] == async_resp['Parameter']


@pytest.mark.asyncio
async def test_pagination_no_kwargs(
    aio_ssm_client: AIOClient,
    param_key: str,
    add_param: None
) -> None:
    param_keys: list = []
    pager = aio_ssm_client.get_paginator("describe_parameters")
    async for page in pager.paginate():
        for param in page['Parameters']:
            param_keys.append(param['Name'])
    
    assert param_key in param_keys


@pytest.mark.asyncio
async def test_pagination_w_kwargs(
    aio_ssm_client: AIOClient,
    param_key: str,
    add_param: None
) -> None:
    kwargs = {
        "ParameterFilters":[
            {
                "Key": "Name", 
                "Option": "BeginsWith", 
                "Values": [
                    "/" + param_key.split("/")[1]
                ]
            }
        ]
    }
    param_keys: list = []
    pager = aio_ssm_client.get_paginator("describe_parameters")
    async for page in pager.paginate(**kwargs):
        for param in page['Parameters']:
            param_keys.append(param['Name'])

    assert param_key in param_keys

    kwargs['ParameterFilters'][0]['Values'] = ["/unknown"]
    param_keys: list = []
    pager = aio_ssm_client.get_paginator("describe_parameters")
    async for page in pager.paginate(**kwargs):
        for param in page['Parameters']:
            param_keys.append(param['Name'])

    assert param_key not in param_keys


@pytest.mark.asyncio
async def test_exception(aio_ssm_client: AIOClient) -> None:
    with pytest.raises(aio_ssm_client.exceptions.ParameterNotFound):
        await aio_ssm_client.get_parameter(Name="/unknown/param")


