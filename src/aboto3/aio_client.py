
import asyncio
from concurrent.futures import ThreadPoolExecutor
import types
from typing import Any, Dict, Optional

from aboto3.aio_paginator import AIOPaginator


class AIOClient:

    def __init__(
        self, 
        boto3_client, 
        thread_pool_executor: Optional[ThreadPoolExecutor] = None
    ):
        self.client = boto3_client
        self.exceptions = self.client.exceptions
        if thread_pool_executor is None:
            self._thread_pool = ThreadPoolExecutor(max_workers=boto3_client._client_config.max_pool_connections)
        else:
            self._thread_pool = thread_pool_executor
    

    def __getattr__(self, name: str) -> Any:
        if hasattr(self.client, name) is True:
            async def client_method(self, **kwargs) -> Any:
                method = name
                return await self.call(method=method, method_kwargs=kwargs)
            
            client_method.__name__ = name
            setattr(self, name, types.MethodType(client_method, self))

            return getattr(self, name)
        
        getattr(self.client, name)
    
    
    async def call(self, method: str, method_kwargs: Dict[str, Any]) -> Any:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            self._thread_pool,
            self._client_call,
            method,
            method_kwargs
        )
    

    def get_paginator(self, method: str) -> AIOPaginator:
        return AIOPaginator(
            thread_pool_executor=self._thread_pool, 
            paginator=self.client.get_paginator(method)
        )


    def _client_call(self, method: str, method_kwargs: Dict[str, Any]) -> Any:
        return getattr(self.client, method)(**method_kwargs)

