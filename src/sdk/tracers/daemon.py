# Standard library
import asyncio
from collections import deque
import json
from threading import Thread
from typing import (
    Any,
    Deque,
    Dict,
)

# Third party libraries
import aiohttp
import aiogqlc
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
    while True:
        if GRAPHQL_CLIENT:
            await asyncio.sleep(1.0)

            results = tuple(iter_except(_RESULTS_QUEUE.pop, IndexError))

            if results:
                send_result_to_server(
                    client=GRAPHQL_CLIENT,
                    query="""
                        mutation(
                            $transactions: [TransactionInput!]!
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
                                totalTime=str(delta(
                                    result.stack[0].timestamp,
                                    result.stack[-1].timestamp,
                                )),
                            )
                            for result in results
                        ],
                    ),
                )


def send_result_to_daemon(
    *,
    result: DaemonResult,
) -> None:
    _RESULTS_QUEUE.appendleft(result)


async def send_result_to_server(
    *,
    client: aiogqlc.GraphQLClient,
    query: str,
    variables: Dict[str, Any],
) -> bool:
    success: bool

    try:
        await client.execute(
            query=query,
            variables=variables
        )
    except aiohttp.ClientError:
        success = False
    else:
        success = True

    return success


# Side effect: Start an asynchronous daemon server
Thread(
    daemon=True,
    name='Tracers Daemon',
    target=lambda: asyncio.run(daemon()),
).start()
