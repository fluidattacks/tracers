# Standard library
from decimal import (
    Decimal,
)
from typing import (
    Any,
    NamedTuple,
    Tuple,
)

# Local libraries
import tracers.function
import backend.dal.aws.dynamodb

# Containers
Transaction = NamedTuple('Transaction', [
    ('initiator', str),
    ('stack', Tuple[Any, ...]),
    ('stdout', str),
    ('tenant_id', str),
    ('total_time', float),
])


@tracers.function.trace()
async def put(
    *,
    transactions: Tuple[Transaction, ...],
) -> bool:
    success = await backend.dal.aws.dynamodb.put(items=[
        backend.dal.aws.dynamodb.Item(
            attributes=dict(
                stack=transaction.stack,
                total_time=transaction.total_time,
            ),
            hash_key=f'tenant:{transaction.tenant_id}/transaction',
            range_key=transaction.initiator,
        )
        for transaction in transactions
    ])

    return success
