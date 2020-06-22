# Standard library
import contextlib
import os
from typing import (
    Any,
    Dict,
    List,
    NamedTuple,
    Optional,
)

# Third party libraries
import aioboto3
from boto3.dynamodb.conditions import (
    Key,
)

# Constants
CONFIG = dict(
    service_name='dynamodb',
    aws_access_key_id=os.environ['AWS_ACCESS_KEY_ID'],
    aws_secret_access_key=os.environ['AWS_SECRET_ACCESS_KEY'],
    aws_session_token=os.environ.get('AWS_SESSION_TOKEN'),
    region_name=os.environ['AWS_DEFAULT_REGION'],
)


# Containers
class Item(NamedTuple):
    hash_key: str
    range_key: str
    attributes: Dict[str, Any] = {}


@contextlib.asynccontextmanager
async def _table():
    async with aioboto3.resource(**CONFIG) as resource:
        yield await resource.Table('main')


async def query(
    hash_key: str,
    range_key: Optional[str] = None,
    attributes_to_get: Optional[List[str]] = None,
) -> List[Item]:
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

    return [
        Item(
            hash_key=result.pop('hash_key'),
            range_key=result.pop('range_key'),
            attributes=result,
        )
        for result in result['Items']
    ]


async def put(items: List[Item]):
    async with _table() as table:
        async with table.batch_writer(
            overwrite_by_pkeys=['hash_key', 'range_key'],
        ) as batch:
            for item in items:
                await batch.put_item(Item=dict(
                    hash_key=item['hash_key'],
                    range_key=item['range_key'],
                    **item['attributes'],
                ))