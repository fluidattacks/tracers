# Standard library
from typing import (
    Any,
    NamedTuple,
    Tuple,
)

# Third party libraries
import tracers.function

# Local libraries
import backend.authc.claims
import backend.config
import backend.dal.aws.dynamodb

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

    success = await backend.dal.aws.dynamodb.put(
        expires_in=backend.config.TRANSACTIONS_TTL,
        items=tuple(
            backend.dal.aws.dynamodb.Item(
                attributes=dict(
                    stack=transaction.stack,
                    total_time=transaction.total_time,
                ),
                hash_key=hash_key,
                range_key=transaction.initiator,
            )
            for transaction in transactions
        ),
    )

    return success
