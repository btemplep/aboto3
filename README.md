# `aboto3`

`aboto3` is an async boto3 client generator!

There are other boto3-like libraries that offer asyncio but the interface can be quite different from normal `boto3` clients. 
The goal of `aboto3` is to closely replicate the `boto3` client interface with similar performance to other asyncio libraries!  

> **NOTE** - `aboto3` was created with performance in mind.  Because of this it does not support [`boto3` "Resources"](https://boto3.amazonaws.com/v1/documentation/api/latest/guide/resources.html), and there is no plan to support them. New "Resources" are no longer being added to `boto3`.


## Tutorial

To create an async client simply pass in the normal `boto3` client to create an `AIOClient`.  

Use the async client, in a coroutine, like you would if the boto3 client's API calls were all async!  See [`boto3` docs](https://boto3.amazonaws.com/v1/documentation/api/latest/index.html) for details.

```python
import asyncio

import aboto3
import boto3

# create a normal boto3 client
ec2_client = boto3.client("ec2")
# create the asyncio version from the client
aio_ec2_client = aboto3.AIOClient(ec2_client)

# you can still use the other client as usual
instances = ec2_client.describe_instances()

# the async client must be used in a coroutine
# but acts exactly the same as the boto3 client except method calls are async
async def aio_tester():
    aio_instances = await aio_ec2_client.describe_instances()

    return aio_instances


aio_instances = asyncio.run(aio_tester())
```

Pass in parameters to the coroutine like a normal client.

```python
import asyncio

import aboto3
import boto3

ec2_client = boto3.client("ec2")
aio_ec2_client = aboto3.AIOClient(ec2_client)


instances = ec2_client.describe_instances(InstanceIds=["i-123412341234"])


async def aio_tester():
    aio_instances = await aio_ec2_client.describe_instances(InstanceIds=["i-123412341234"])

    return aio_instances


aio_instances = asyncio.run(aio_tester())
```

Get an async paginator from the `aboto3` client.

```python
import asyncio

import aboto3
import boto3

ec2_client = boto3.client("ec2")
aio_ec2_client = aboto3.AIOClient(ec2_client)
filters = [
    {
        "Name": "instance-type",
        "Values": [
            "t2.micro"
        ]
    }
]

pages = []
pager = ec2_client.get_paginator("describe_instances")
for page in pager.paginate(Filters=filters):
    pages.append(page)

# note the use of an "async for" loop so calls for a page are non-blocking.
async def aio_tester():
    aio_pages = []
    aio_pager = aio_ec2_client.get_paginator("describe_instances")
    async for page in aio_pager.paginate(Filters=filters):
        aio_pages.append(page)

    return aio_pages


aio_pages = asyncio.run(aio_tester())
```

Client exceptions can be caught on the `AIOClient` just like a normal `boto3` client.
`botocore` exceptions are caught as normal.

```python
import asyncio

import aboto3
import boto3

ssm_client = boto3.client("ssm")
aio_ssm_client = aboto3.AIOClient(ssm_client)

try:
    ssm_client.get_parameter(Name="/unknown/param")
except ssm_client.exceptions.ParameterNotFound as error:
    print("found an error here: {}".format(error))


async def aio_tester():
    try:
        aio_ssm_client.get_parameter(Name="/unknown/param")
    except aio_ssm_client.exceptions.ParameterNotFound as error:
        print("found an error here: {}".format(error))


aio_pages = asyncio.run(aio_tester())
```

You can also use `boto3` augmenting libraries since `aboto3` is only a wrapper. 

Like [`aws-assume-role-lib`](https://github.com/benkehoe/aws-assume-role-lib) for easily assuming roles and
automatically refreshing credentials.

```python
import asyncio

import aboto3
from aws_assume_role_lib import assume_role
import boto3

sess = boto3.Session()
assumed_sess = assume_role(
    session=sess, 
    RoleArn="arn:aws:iam::123123123123:role/my_role_to_assume", 
    RoleSessionName="tester_short", 
    DurationSeconds=900
)

ec2_client = assumed_sess.client("ec2")
aio_ec2_client = aboto3.AIOClient(ec2_client)
```


## Optimization 

When an `AIOClient` is created it will automatically create a `ThreadPoolExecutor` to run the boto3 calls asynchronously.  The size of max workers of the pool is determined by the boto3 client's config for `max_pool_connections`. By default this is 10.
See [botocore Config Reference](https://botocore.amazonaws.com/v1/documentation/api/latest/reference/config.html#botocore-config) for more details.

> **NOTE** - Because `aboto3` provides an async wrapper around `boto3`, it is not truly async to it's core. It sends a boto3 call to a thread and the thread runs asynchronously. There may be a limit to this as asyncio Tasks are generally lighter weight than threads. 

The thread pool adds a small amount of overhead for each `AIOClient` that is created (though this is far less than the overhead of creating a boto3 client).  To save some initialization time or have more control over total number of threads you can provide your own `ThreadPoolExecutor` and share this between clients.


```python
import asyncio
from concurrent.futures import ThreadPoolExecutor

import aboto3
import boto3

boto3_thread_pool = ThreadPoolExecutor(max_workers=16)

ec2_client = boto3.client("ec2")
aio_ec2_client = AIOClient(
    boto3_client=ec2_client, 
    thread_pool_executor=boto3_thread_pool
)

rds_client = boto3.client("rds")
aio_rds_client = AIOClient(
    boto3_client=rds_client, 
    thread_pool_executor=boto3_thread_pool
)

```

In general, for applications, you will want to cache the clients if possible. Try not to create a new one in every function. For applications, a shared thread pool can be useful in limiting the total number of threads, when necessary. 

If you are making large numbers of concurrent calls with the same `AIOClient` you may want to pass in a custom `botocore.config.Config` to the boto3 client with a higher `max_pool_connections`.  If you are using a shared thread pool you may also need to increase the max workers in that as well. 

The example below will allow up to 32 concurrent calls to be in flight for the EC2 and RDS `AIOClient`'s.

```python
import asyncio
from concurrent.futures import ThreadPoolExecutor

import aboto3
import boto3
from botocore.config import Config

boto_config = Config(
    max_pool_connections=32
)
boto3_thread_pool = ThreadPoolExecutor(max_workers=64)

ec2_client = boto3.client("ec2", config=boto_config)
aio_ec2_client = AIOClient(
    boto3_client=ec2_client, 
    thread_pool_executor=boto3_thread_pool
)
rds_client = boto3.client("rds", config=boto_config)
aio_rds_client = AIOClient(
    boto3_client=rds_client, 
    thread_pool_executor=boto3_thread_pool
)

```

Or if you don't care about sharing the thread pool just pass in the config 
and each `AIOClient` will have it's own pool of 32 threads. 

```python
import asyncio

import aboto3
import boto3
from botocore.config import Config

boto_config = Config(
    max_pool_connections=32
)

ec2_client = boto3.client("ec2", config=boto_config)
aio_ec2_client = AIOClient(boto3_client=ec2_client)

rds_client = boto3.client("rds", config=boto_config)
aio_rds_client = AIOClient(boto3_client=rds_client)
```


## Development

Install the package in editable mode with dev dependencies.

```text
(venv) $ pip install -e .[dev]
```

[`nox`](https://nox.thea.codes/en/stable/) is used to manage various dev functions.
Start with

```text
(venv) $ nox --help
```

[`pyenv`](https://github.com/pyenv/pyenv) is used to manage python versions. 
To run the nox tests for applicable python version you will first need to install them. 
In the root project dir run:

```text
(venv) $ pyenv install
```
