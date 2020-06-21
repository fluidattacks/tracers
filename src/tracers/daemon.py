# Standard library
import asyncio
from collections import deque
from threading import Thread

# Third party imports
from more_itertools import iter_except

# Local imports


# Private constants
_RESULTS_QUEUE: deque = deque()


async def daemon():
    while True:
        await asyncio.sleep(1.0)
        tuple(iter_except(_RESULTS_QUEUE.pop, IndexError))


def send_result_to_daemon(result):
    _RESULTS_QUEUE.appendleft(result)


# Side effect: Start an asynchronous daemon server
Thread(daemon=True, target=lambda: asyncio.run(daemon())).start()
