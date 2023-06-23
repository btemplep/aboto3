import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Any, AsyncIterable


class AIOPageIterator:


    def __init__(
        self,
        thread_pool_executor: ThreadPoolExecutor,
        page_iterator
    ):
        self._thread_pool = thread_pool_executor
        self._page_iterator = page_iterator
        self._iter_page_iterable = None

    
    def __aiter__(self) -> AsyncIterable:
        self._iter_page_iterable = iter(self._page_iterator)

        return self


    async def __anext__(self) -> Any:
        loop = asyncio.get_running_loop()

        return await loop.run_in_executor(
            self._thread_pool,
            self._get_next_page
        )


    def _get_next_page(self) -> Any:
        try:
            return next(self._iter_page_iterable)
        except StopIteration as error:
            raise StopAsyncIteration(error)

