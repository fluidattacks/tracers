# Standard library
import asyncio
from collections import deque
from multiprocessing import Process
from typing import (
    Deque,
)

# Third party libraries
from more_itertools import iter_except

# Local libraries
from tracers.containers import (
    DaemonResult,
)

# Private constants
_RESULTS_QUEUE: Deque[DaemonResult] = deque()


async def daemon() -> None:
    while True:
        await asyncio.sleep(1.0)
        tuple(iter_except(_RESULTS_QUEUE.pop, IndexError))


def send_result_to_daemon(result: DaemonResult) -> None:
    _RESULTS_QUEUE.appendleft(result)


# Side effect: Start an asynchronous daemon server
Process(daemon=True, target=lambda: asyncio.run(daemon())).start()
