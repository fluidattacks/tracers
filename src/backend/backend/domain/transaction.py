# Standard library
from typing import (
    Any,
    List,
    NamedTuple,
)

# Local libraries
import backend.dal.aws.dynamodb

# Containers
Transaction = NamedTuple('Transaction', [
    ('initiator', str),
    ('stack', List[Any]),
    ('stdout', str),
    ('tenant_id', str),
    ('total_time', float),
])


async def put(
    *,
    transactions: List[Transaction],
) -> bool:
    success = await backend.dal.aws.dynamodb.put(items=[
        backend.dal.aws.dynamodb.Item(
            attributes=dict(
                stack=transaction.stack,
                stdout=transaction.stdout,
                total_time=transaction.total_time,
            ),
            hash_key=f'tenant:{transaction.tenant_id}/transaction',
            range_key=transaction.initiator,
        )
        for transaction in transactions
    ])

    return success
