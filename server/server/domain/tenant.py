# Standard library
from typing import (
    Tuple,
)
from uuid import uuid4 as uuid

# Third party libraries
import tracers.function
from boto3.dynamodb.conditions import (
    Attr,
)

# Local libraries
import server.api.schema.types
import server.config
import server.dal.aws.dynamodb
import server.utils.aio
import server.utils.crypto


@tracers.function.trace()
async def get_tenant_credential(
    *,
    tenant_id: str,
) -> Tuple[server.api.schema.types.Transaction, ...]:
    results = await server.dal.aws.dynamodb.query(
        hash_key=await server.dal.aws.dynamodb.serialize_key({
            'type': 'tenant',
            'tenant_id': tenant_id,
        }),
        range_key=await server.dal.aws.dynamodb.serialize_key({
            'type': 'credential',
        }),
    )

    return tuple(
        server.api.schema.types.UserCredential(
            tenant_id=tenant_id,
            tenant_secret_hash=result['tenant_secret_hash'],
            tenant_secret_salt=result['tenant_secret_salt'],
        )
        for result in results
    )


@tracers.function.trace()
async def put_tenant_credential(
    *,
    tenant_id: str,
    tenant_secret: str,
) -> bool:
    tenant_secret_salt: str = server.utils.crypto.get_salt()
    tenant_secret_hash: str = server.utils.crypto.get_hash(
        string=tenant_secret,
        salt=tenant_secret_salt,
    )

    return await server.dal.aws.dynamodb.put((
        server.dal.aws.dynamodb.Request(
            condition_expression=(
                Attr('hash_key').not_exists()
            ),
            expression_attribute_values={
                ':tenant_secret_hash': tenant_secret_hash,
                ':tenant_secret_salt': tenant_secret_salt,
            },
            hash_key=await server.dal.aws.dynamodb.serialize_key({
                'type': 'tenant',
                'tenant_id': tenant_id,
            }),
            range_key=await server.dal.aws.dynamodb.serialize_key({
                'type': 'credential',
            }),
            update_expression={
                'SET': {
                    'tenant_secret_hash = :tenant_secret_hash',
                    'tenant_secret_salt = :tenant_secret_salt',
                },
            },
        ),
    ))
