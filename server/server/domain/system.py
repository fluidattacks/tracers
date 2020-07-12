# Standard library
from datetime import (
    datetime,
)
from typing import (
    Tuple,
)

# Third party libraries
import tracers.function
from boto3.dynamodb.conditions import (
    Attr,
)

# Local libraries
import server.api.schema.types
import server.authc.claims
import server.config
import server.dal.aws.dynamodb
import server.utils.aio


@tracers.function.trace()
async def _get_intervals() -> Tuple[Tuple[int, str], ...]:
    now: float = datetime.utcnow().timestamp()

    stamps: Tuple[Tuple[int, str], ...] = tuple(
        (interval,
         datetime.utcfromtimestamp(interval * (now // interval)).isoformat())
        for interval in server.config.MEASURE_INTERVALS
    )

    return stamps


@tracers.function.trace()
async def get_system_measure__transaction(
    *,
    claims: server.authc.claims.TracersTenant,
    interval: int,
    system_id: str,
) -> Tuple[server.api.schema.types.Transaction, ...]:
    hash_key: str = server.dal.aws.dynamodb.serialize_key({
        'interval': str(interval),
        'system_id': system_id,
        'tenant_id': claims.tenant_id,
        'type': 'system_measure',
    })
    range_key: str = server.dal.aws.dynamodb.serialize_key({
        'type': 'transaction',
    })
    results = await server.dal.aws.dynamodb.query(
        hash_key=hash_key,
        range_key=range_key,
    )

    return tuple(server.api.schema.types.Transaction(
        initiator=result['range_key']['initiator'],
        max_stack=result['max_stack'],
        max_total_time=result['max_total_time'],
        min_stack=result['min_stack'],
        min_total_time=result['min_total_time'],
        stamp=result['range_key']['stamp'],
    ) for result in results)


@tracers.function.trace()
async def put_tenant__system(
    *,
    claims: server.authc.claims.TracersTenant,
    system_id: str,
) -> bool:
    return await server.dal.aws.dynamodb.put((
        server.dal.aws.dynamodb.Request(
            allow_condition_failure=True,
            expires_in=(
                server.config.MEASURE_INTERVALS[-1] *
                server.config.TTL_PER_SECOND
            ),
            hash_key=server.dal.aws.dynamodb.serialize_key({
                'tenant_id': claims.tenant_id,
                'type': 'tenant',
            }),
            range_key=server.dal.aws.dynamodb.serialize_key({
                'type': 'system',
                'system_id': system_id,
            }),
        ),
    ))


@tracers.function.trace()
async def put_system_measure__transactions(
    *,
    claims: server.authc.claims.TracersTenant,
    system_id: str,
    transactions: Tuple[server.api.schema.types.TransactionInput, ...],
) -> bool:
    intervals = await _get_intervals()

    return all(await server.utils.aio.materialize([
        put_system_measure__transaction(
            hash_key=server.dal.aws.dynamodb.serialize_key({
                'interval': str(interval),
                'system_id': system_id,
                'tenant_id': claims.tenant_id,
                'type': 'system_measure',
            }),
            interval=interval,
            stamp=stamp,
            transaction=transaction,
        )
        for transaction in transactions
        for interval, stamp in intervals
    ]))


@tracers.function.trace()
async def put_system_measure__transaction(
    *,
    hash_key: str,
    interval: int,
    stamp: str,
    transaction: server.api.schema.types.TransactionInput,
) -> bool:
    range_key: str = server.dal.aws.dynamodb.serialize_key({
        'type': 'transaction',
        'initiator': transaction.initiator,
        'stamp': stamp,
    })

    return await server.dal.aws.dynamodb.put((
        # Initialize the item if it does not exist
        server.dal.aws.dynamodb.Request(
            allow_condition_failure=True,
            condition_expression=(
                Attr('hash_key').not_exists()
                & Attr('range_key').not_exists()
            ),
            expires_in=interval * server.config.TTL_PER_SECOND,
            expression_attribute_values={
                ':stack': transaction.stack,
                ':total_time': transaction.total_time,
            },
            hash_key=hash_key,
            range_key=range_key,
            update_expression={
                'SET': {
                    'min_stack = :stack',
                    'min_total_time = :total_time',
                    'max_stack = :stack',
                    'max_total_time = :total_time',
                },
            },
        ),
        # Update the minimun transaction
        server.dal.aws.dynamodb.Request(
            allow_condition_failure=True,
            condition_expression=(
                Attr('min_total_time').exists()
                & Attr('min_total_time').gt(transaction.total_time)
            ),
            expression_attribute_values={
                ':stack': transaction.stack,
                ':total_time': transaction.total_time,
            },
            hash_key=hash_key,
            range_key=range_key,
            update_expression={
                'SET': {
                    'min_stack = :stack',
                    'min_total_time = :total_time',
                },
            },
        ),
        # Update the maximum transaction
        server.dal.aws.dynamodb.Request(
            allow_condition_failure=True,
            condition_expression=(
                Attr('max_total_time').exists()
                & Attr('max_total_time').lt(transaction.total_time)
            ),
            expression_attribute_values={
                ':stack': transaction.stack,
                ':total_time': transaction.total_time,
            },
            hash_key=hash_key,
            range_key=range_key,
            update_expression={
                'SET': {
                    'max_stack = :stack',
                    'max_total_time = :total_time',
                },
            },
        ),
    ))
