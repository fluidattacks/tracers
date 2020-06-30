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
import backend.api.schema.types
import backend.authc.claims
import backend.config
import backend.dal.aws.dynamodb
import backend.utils.aio


@tracers.function.trace()
async def _get_intervals() -> Tuple[Tuple[int, str], ...]:
    now: float = datetime.utcnow().timestamp()

    stamps: Tuple[Tuple[int, str], ...] = tuple(
        (interval,
         datetime.utcfromtimestamp(interval * (now // interval)).isoformat())
        for interval in backend.config.MEASURE_INTERVALS
    )

    return stamps


@tracers.function.trace()
async def get(
    *,
    claims: backend.authc.claims.TracersTenant,
    interval: int,
    system_id: str,
) -> Tuple[backend.api.schema.types.Transaction, ...]:
    hash_key: str = backend.dal.aws.dynamodb.serialize_key({
        'type': 'tenant_systems',
        'tenant_id': claims.tenant_id,
        'system_id': system_id,
    })
    range_key: str = backend.dal.aws.dynamodb.serialize_key({
        'type': 'measure',
        'interval': str(interval),
    })
    results = await backend.dal.aws.dynamodb.query(
        hash_key=hash_key,
        range_key=range_key,
    )

    return tuple(backend.api.schema.types.Transaction(
        initiator=result['range_key']['initiator'],
        max_stack=result['max_stack'],
        max_total_time=result['max_total_time'],
        min_stack=result['min_stack'],
        min_total_time=result['min_total_time'],
        stamp=result['range_key']['stamp'],
    ) for result in results)


@tracers.function.trace()
async def put_many(
    *,
    claims: backend.authc.claims.TracersTenant,
    system_id: str,
    transactions: Tuple[backend.api.schema.types.TransactionInput, ...],
) -> bool:
    hash_key = backend.dal.aws.dynamodb.serialize_key({
        'type': 'tenant_systems',
        'tenant_id': claims.tenant_id,
        'system_id': system_id,
    })
    intervals = await _get_intervals()

    return all(await backend.utils.aio.materialize([
        put_one_measure(
            hash_key=hash_key,
            interval=interval,
            stamp=stamp,
            transaction=transaction,
        )
        for transaction in transactions
        for interval, stamp in intervals
    ]))


@tracers.function.trace()
async def put_one_measure(
    *,
    hash_key: str,
    interval: int,
    stamp: str,
    transaction: backend.api.schema.types.TransactionInput,
) -> bool:
    range_key: str = backend.dal.aws.dynamodb.serialize_key({
        'type': 'measure',
        'interval': str(interval),
        'initiator': transaction.initiator,
        'stamp': stamp,
    })

    return await backend.dal.aws.dynamodb.put((
        # Initialize the item if it does not exist
        backend.dal.aws.dynamodb.Request(
            allow_condition_failure=True,
            condition_expression=(
                Attr('hash_key').not_exists()
                & Attr('range_key').not_exists()
            ),
            expires_in=interval * backend.config.TTL_PER_SECOND,
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
        backend.dal.aws.dynamodb.Request(
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
        backend.dal.aws.dynamodb.Request(
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
