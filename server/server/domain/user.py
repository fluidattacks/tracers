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
async def get_user_credential(
    *,
    user_id: str,
) -> Tuple[server.api.schema.types.Transaction, ...]:
    results = await server.dal.aws.dynamodb.query(
        hash_key=server.dal.aws.dynamodb.serialize_key({
            'type': 'user',
            'user_id': user_id,
        }),
        range_key=server.dal.aws.dynamodb.serialize_key({
            'type': 'credential',
        }),
    )

    return tuple(
        server.api.schema.types.UserCredential(
            tenant_id=result['tenant_id'],
            user_id=user_id,
            user_secret_hash=result['user_secret_hash'],
            user_secret_salt=result['user_secret_salt'],
        )
        for result in results
    )


@tracers.function.trace()
async def put_user_credential(
    *,
    user_id: str,
    user_secret: str,
) -> bool:
    user_secret_salt: str = server.utils.crypto.get_salt()
    user_secret_hash: str = server.utils.crypto.get_hash(
        string=user_secret,
        salt=user_secret_salt,
    )

    return await server.dal.aws.dynamodb.put((
        server.dal.aws.dynamodb.Request(
            condition_expression=(
                Attr('hash_key').not_exists()
            ),
            expression_attribute_values={
                ':tenant_id': uuid().hex,
                ':user_secret_hash': user_secret_hash,
                ':user_secret_salt': user_secret_salt,
            },
            hash_key=server.dal.aws.dynamodb.serialize_key({
                'type': 'user',
                'user_id': user_id,
            }),
            range_key=server.dal.aws.dynamodb.serialize_key({
                'type': 'credential',
            }),
            update_expression={
                'SET': {
                    'tenant_id = :tenant_id',
                    'user_secret_hash = :user_secret_hash',
                    'user_secret_salt = :user_secret_salt',
                },
            },
        ),
    ))
