# Standard library
import asyncio
from collections import deque
from threading import Thread

# Local libraries
from tracers.utils import (
    drain_queue,
)

# Private constants
_RESULTS_QUEUE: deque = deque()


async def daemon():
    while True:
        await asyncio.sleep(1.0)
        len(drain_queue(_RESULTS_QUEUE))


def send_result_to_daemon(result):
    _RESULTS_QUEUE.appendleft(result)


# Side effect: Start an asynchronous daemon server
Thread(daemon=True, target=lambda: asyncio.run(daemon())).start()
