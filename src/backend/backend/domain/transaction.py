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
async def put(
    *,
    claims: backend.authc.claims.TracersTenant,
    transactions: Tuple[Transaction, ...],
) -> bool:
    hash_key = await backend.dal.aws.dynamodb.build_key(claims._asdict())
    stamp: datetime = datetime.utcnow().replace(microsecond=0)

    return await backend.dal.aws.dynamodb.put(tuple([
        request
        for transaction in transactions
        for interval, bucket_stamp in [
            # Every second
            (1, stamp),
            # Every minute
            (60, stamp.replace(second=0)),
            # Every 5 minutes
            (300, stamp.replace(second=0, minute=5 * (stamp.minute // 5))),
            # Every 15 minutes
            (900, stamp.replace(second=0, minute=15 * (stamp.minute // 15))),
            # Every hour
            (3600, stamp.replace(second=0, minute=0)),
            # Every day
            (86400, stamp.replace(second=0, minute=0, hour=0)),
            # Every month
            (2592000, stamp.replace(second=0, minute=0, hour=0, day=1)),
        ]
        for range_key in [
            await backend.dal.aws.dynamodb.build_key(dict(
                initiator=transaction.initiator,
                interval=str(interval),
                stamp=bucket_stamp.isoformat(),
            )),
        ]
        for request in [
            # Initialize the item if it does not exist
            backend.dal.aws.dynamodb.Request(
                allow_condition_failure=True,
                condition_expression=(
                    Attr('hash_key').not_exists()
                    & Attr('range_key').not_exists()
                ),
                expires_in=interval * backend.config.TTL_PER_SECOND,
                expression_attribute_values={
                    # ':stack': transaction.stack,
                    ':total_time': transaction.total_time,
                },
                hash_key=hash_key,
                range_key=range_key,
                update_expression={
                    'SET': {
                        # 'min_stack = :stack',
                        'min_total_time = :total_time',
                        # 'max_stack = :stack',
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
                    # ':stack': transaction.stack,
                    ':total_time': transaction.total_time,
                },
                hash_key=hash_key,
                range_key=range_key,
                update_expression={
                    'SET': {
                        # 'min_stack = :stack',
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
                    # ':stack': transaction.stack,
                    ':total_time': transaction.total_time,
                },
                hash_key=hash_key,
                range_key=range_key,
                update_expression={
                    'SET': {
                        # 'max_stack = :stack',
                        'max_total_time = :total_time',
                    },
                },
            ),
        ]
    ]))
