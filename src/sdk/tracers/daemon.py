# Standard library
import asyncio
from collections import deque
from decimal import Decimal
import json
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
from tracers.graphql import (
    CLIENT as GRAPHQL_CLIENT,
)
from tracers.utils import (
    delta,
)

# Private constants
_RESULTS_QUEUE: Deque[DaemonResult] = deque()


async def daemon() -> None:
    if GRAPHQL_CLIENT:
        while True:
            await asyncio.sleep(1.0)
            await GRAPHQL_CLIENT.execute(
                query="""
                    mutation PutTransaction(
                        $transactions: [TransactionInput]
                    ) {
                        putTransaction(
                            transactions: $transactions
                        ) {
                            success
                        }
                    }
                    """,
                variables=dict(
                    transactions=[
                        dict(
                            initiator=result.stack[0].function,
                            stack=json.dumps(result.stack),
                            stdout=result.stdout,
                            tenantId='123',
                            totalTime=Decimal(delta(
                                result.stack[0].timestamp,
                                result.stack[-1].timestamp,
                            )),
                        )
                        for result in iter_except(
                            _RESULTS_QUEUE.pop, IndexError,
                        )
                    ]
                ),
            )


def send_result_to_daemon(result: DaemonResult) -> None:
    _RESULTS_QUEUE.appendleft(result)


# Side effect: Start an asynchronous daemon server
Process(daemon=True, target=lambda: asyncio.run(daemon())).start()
