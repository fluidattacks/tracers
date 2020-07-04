# Standard library
import asyncio
from collections import deque
from threading import Thread
from typing import (
    Any,
    Deque,
    Dict,
    Tuple,
)

# Third party libraries
import aiohttp
import aiogqlc
from more_itertools import iter_except

# Local libraries
from tracers.config import (
    CONFIG,
)
from tracers.constants import (
    LOGGER_DAEMON,
)
from tracers.containers import (
    DaemonResult,
)
from tracers.graphql import (
    CLIENT as GRAPHQL_CLIENT,
)
from tracers.utils import (
    delta,
    json_dumps,
)

# Private constants
_RESULTS_QUEUE: Deque[DaemonResult] = deque()


async def daemon() -> None:
    if GRAPHQL_CLIENT:
        success, msg = await send_system_to_server(client=GRAPHQL_CLIENT)

        if success:
            LOGGER_DAEMON.info('New system created: %s', CONFIG.system_id)
        else:
            LOGGER_DAEMON.error('Error creating system: %s', msg)

    while await asyncio.sleep(1.0, result=True):
        results = tuple(iter_except(_RESULTS_QUEUE.pop, IndexError))
        results_len = len(results)

        if GRAPHQL_CLIENT and results:
            success, msg = await send_transactions_to_server(
                client=GRAPHQL_CLIENT,
                results=results,
            )

            if success:
                LOGGER_DAEMON.info('Uploaded transactions: %s', results_len)
            else:
                LOGGER_DAEMON.error('Uploading transactions: %s', msg)


def send_result_to_daemon(
    *,
    result: DaemonResult,
) -> None:
    _RESULTS_QUEUE.appendleft(result)


async def request_server(
    *,
    client: aiogqlc.GraphQLClient,
    query: str,
    variables: Dict[str, Any] = {},
) -> Tuple[bool, str]:
    msg: str
    success: bool

    try:
        await client.execute(query=query, variables=variables)
    except aiohttp.ClientError as exception:
        msg, success = str(exception), False
    else:
        msg, success = '', True

    return success, msg


async def send_system_to_server(
    *,
    client: aiogqlc.GraphQLClient,
) -> Tuple[bool, str]:
    return await request_server(
        client=client,
        query="""
            mutation(
                $systemId: String!
            ) {
                putSystem(
                    systemId: $systemId
                ) {
                    success
                }
            }
        """,
        variables={
            'systemId': CONFIG.system_id,
        },
    )


async def send_transactions_to_server(
    *,
    client: aiogqlc.GraphQLClient,
    results: Tuple[DaemonResult, ...],
) -> Tuple[bool, str]:
    return await request_server(
        client=client,
        query="""
            mutation(
                $systemId: String!
                $transactions: [TransactionInput!]!
            ) {
                putTransactions(
                    systemId: $systemId
                    transactions: $transactions
                ) {
                    success
                }
            }
        """,
        variables={
            'systemId': CONFIG.system_id,
            'transactions': [
                {
                    'initiator': result.stack[0].function,
                    'stack': json_dumps(result.stack),
                    'totalTime': str(delta(
                        result.stack[0].timestamp,
                        result.stack[-1].timestamp,
                    )),
                }
                for result in results
            ],
        },
    )


# Side effect: Start an asynchronous daemon server
Thread(
    daemon=True,
    name='Tracers Daemon',
    target=lambda: asyncio.run(daemon()),
).start()
