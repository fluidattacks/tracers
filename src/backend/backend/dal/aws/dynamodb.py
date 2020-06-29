# Standard library
import contextlib
import os
import time
from typing import (
    Any,
    Dict,
    List,
    NamedTuple,
    Optional,
    Tuple,
)

# Third party libraries
import aioboto3
import aioboto3.dynamodb.table
from boto3.dynamodb.conditions import (
    Key,
)

# Local libraries
import tracers.function

# Constants
CONFIG = dict(
    aws_access_key_id=os.environ['AWS_ACCESS_KEY_ID'],
    aws_secret_access_key=os.environ['AWS_SECRET_ACCESS_KEY'],
    aws_session_token=os.environ.get('AWS_SESSION_TOKEN'),
    endpoint_url='http://localhost:8022',
    region_name=os.environ['AWS_DEFAULT_REGION'],
    service_name='dynamodb',
)


# Containers
class Item(NamedTuple):
    hash_key: str
    range_key: str
    attributes: Dict[str, Any] = {}


@tracers.function.trace()
@contextlib.asynccontextmanager
async def _table() -> aioboto3.dynamodb.table.TableResource:
    async with aioboto3.resource(**CONFIG) as resource:
        yield await resource.Table('main')


@tracers.function.trace()
async def query(
    *,
    hash_key: str,
    range_key: Optional[str] = None,
    attributes_to_get: Optional[Tuple[str, ...]] = None,
) -> Tuple[Item, ...]:
    results: List[object] = []

    condition = Key('hash_key').eq(hash_key)
    if range_key:
        condition &= Key('range_key').eq(range_key)

    async with _table() as table:
        params = dict(
            AttributesToGet=attributes_to_get,
            KeyConditionExpression=condition,
        )

        result = await table.query(**params)
        results.extend(result['Items'])

        while 'LastEvaluatedKey' in result:
            params['LastEvaluatedKey'] = result['LastEvaluatedKey']

            result = await table.query(**params)
            results.extend(result['Items'])

    return tuple(
        Item(
            hash_key=result.pop('hash_key'),
            range_key=result.pop('range_key'),
            attributes=result,
        )
        for result in result['Items']
    )


@tracers.function.trace()
async def put(
    *,
    expires_in: Optional[float] = None,
    items: Tuple[Item, ...],
) -> bool:
    success: bool = True

    async with _table() as table:
        async with table.batch_writer(
            overwrite_by_pkeys=['hash_key', 'range_key'],
        ) as batch:
            for item in items:
                if expires_in:
                    item.attributes['ttl'] = int(time.time()) + expires_in

                await batch.put_item(Item=dict(
                    hash_key=item.hash_key,
                    range_key=item.range_key,
                    **item.attributes,
                ))

    return success
