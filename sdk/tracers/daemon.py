# Standard library
import asyncio
from multiprocessing import (
    Process,
    Queue,
)
from queue import Empty
from typing import (
    Any,
    Dict,
    Tuple,
)

# Third party libraries
import aiohttp
import aiogqlc
from more_itertools import iter_except

# Local libraries
from tracers.analyzers import (
    analyze_loop_snapshots,
    analyze_stack,
)
from tracers.config import (
    CONFIG,
)
from tracers.containers import (
    DaemonResult,
)
from tracers.graphql import (
    CLIENT as GRAPHQL_CLIENT,
)
from tracers.utils import (
    delta,
    log,
    json_dumps,
)

# Private constants
_RESULTS_QUEUE: Queue = Queue()  # type: ignore


async def daemon() -> None:
    if GRAPHQL_CLIENT:
        success, msg = await send_system_to_server(client=GRAPHQL_CLIENT)

        if not success:
            log(f'Error creating system: {msg}', level='error')

    while await asyncio.sleep(CONFIG.daemon_interval, result=True):
        results = tuple(iter_except(_RESULTS_QUEUE.get_nowait, Empty))

        if GRAPHQL_CLIENT and results:
            for result in results:
                analyze_stack(result.stack)
                analyze_loop_snapshots(result.loop_snapshots)

            success, msg = await send_transactions_to_server(
                client=GRAPHQL_CLIENT,
                results=results,
            )

            if not success:
                log(f'Uploaded transactions: {msg}', level='error')


def send_result_to_daemon(
    *,
    result: DaemonResult,
) -> None:
    _RESULTS_QUEUE.put_nowait(result)


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
                putSystemTransactions(
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
Process(
    daemon=True,
    name='Tracers Daemon',
    target=lambda: asyncio.run(daemon()),
).start()
