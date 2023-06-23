
from concurrent.futures import ThreadPoolExecutor

from aboto3.aio_page_iterator import AIOPageIterator


class AIOPaginator:

    def __init__(
        self, 
        thread_pool_executor: ThreadPoolExecutor, 
        paginator
    ):
        self._thread_pool = thread_pool_executor
        self._paginator = paginator
    

    def paginate(self, **kwargs) -> AIOPageIterator:
        return AIOPageIterator(
            thread_pool_executor=self._thread_pool,
            page_iterator=self._paginator.paginate(**kwargs)
        )

