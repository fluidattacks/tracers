# Standard library
from datetime import (
    datetime,
)
from typing import (
    Any,
    NamedTuple,
    Tuple,
)

# Third party libraries
import tracers.function
from boto3.dynamodb.conditions import (
    Attr,
)

# Local libraries
import backend.authc.claims
import backend.config
import backend.dal.aws.dynamodb
import backend.utils.aio

# Containers
Transaction = NamedTuple('Transaction', [
    ('initiator', str),
    ('stack', Tuple[Any, ...]),
    ('total_time', float),
])


@tracers.function.trace()
@backend.utils.aio.to_async
def _get_intervals() -> Tuple[Tuple[int, str], ...]:
    now: float = datetime.utcnow().timestamp()

    stamps: Tuple[Tuple[int, str], ...] = tuple(
        (interval,
         datetime.utcfromtimestamp(interval * (now // interval)).isoformat())
        for interval in backend.config.MEASURE_INTERVALS
    )

    return stamps


@tracers.function.trace()
async def put(
    *,
    claims: backend.authc.claims.TracersTenant,
    transactions: Tuple[Transaction, ...],
) -> bool:
    hash_key = await backend.dal.aws.dynamodb.build_key(claims._asdict())
    intervals = await _get_intervals()

    return await backend.utils.aio.materialize(tuple(
        _put_one(
            hash_key=hash_key,
            interval=interval,
            stamp=stamp,
            transaction=transaction,
        )
        for transaction in transactions
        for interval, stamp in intervals
    ))


@tracers.function.trace()
async def _put_one(
    *,
    hash_key: str,
    interval: int,
    stamp: str,
    transaction: Transaction,
):
    range_key: str = await backend.dal.aws.dynamodb.build_key({
        'initiator': transaction.initiator,
        'interval': str(interval),
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
