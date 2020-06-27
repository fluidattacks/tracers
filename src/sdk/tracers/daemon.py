# Standard library
import asyncio
from collections import deque
import json
from threading import Thread
from typing import (
    Deque,
    Tuple,
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
    log_stderr,
)

# Private constants
_RESULTS_QUEUE: Deque[DaemonResult] = deque()


async def daemon() -> None:
    while await asyncio.sleep(1.0, result=True):
        results = tuple(iter_except(_RESULTS_QUEUE.pop, IndexError))
        results_len = len(results)

        if GRAPHQL_CLIENT and results:
            success, msg = await send_results_to_server(
                client=GRAPHQL_CLIENT,
                results=results,
            )

            if success:
                log_stderr(f'[DAEMON] Uploaded transactions: {results_len}')
            else:
                log_stderr(f'[DAEMON] Error uploading: {msg}')


def send_result_to_daemon(
    *,
    result: DaemonResult,
) -> None:
    _RESULTS_QUEUE.appendleft(result)


async def send_results_to_server(
    *,
    client: aiogqlc.GraphQLClient,
    results: Tuple[DaemonResult, ...],
) -> Tuple[bool, str]:
    try:
        await client.execute(
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
    except aiohttp.ClientError as exception:
        msg: str = str(exception)
        success: bool = False
    else:
        msg = ''
        success = True

    return success, msg


# Side effect: Start an asynchronous daemon server
Thread(
    daemon=True,
    name='Tracers Daemon',
    target=lambda: asyncio.run(daemon()),
).start()
