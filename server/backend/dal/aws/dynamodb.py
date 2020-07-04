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
    Set,
    Tuple,
)

# Third party libraries
import aioboto3
import aioboto3.dynamodb.table
import botocore.exceptions
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
class Request(NamedTuple):
    hash_key: str
    range_key: str

    allow_condition_failure: bool = False
    condition_expression: Optional[Any] = None
    expires_in: Optional[float] = None
    expression_attribute_names: Dict[str, Any] = {}
    expression_attribute_values: Dict[str, Any] = {}
    update_expression: Dict[str, Set[str]] = {}


@tracers.function.trace()
def serialize_key(key: Dict[str, str]) -> str:
    if not key:
        raise ValueError('Empty parameters')

    if not all(
        isinstance(obj, str)
        for arguments in key.items()
        for obj in arguments
    ):
        raise TypeError(f'Expected Dict[str, str], got: {type(key)}')

    return '/'.join(
        f'{attribute_name.encode().hex()}:{attribute_value.encode().hex()}'
        for attribute_name, attribute_value in key.items()
    )


@tracers.function.trace()
def deserialize_key(key: str) -> Dict[str, str]:
    if not isinstance(key, str):
        raise TypeError(f'Expected str, got: {type(key)}')

    return {
        bytes.fromhex(attribute_name).decode():
        bytes.fromhex(attribute_value).decode()
        for attribute in key.split('/')
        for attribute_name, attribute_value in [attribute.split(':')]
    }


@tracers.function.trace()
async def query(
    *,
    hash_key: str,
    range_key: Optional[str] = None,
    attributes_to_get: Optional[Tuple[str, ...]] = None,
) -> Tuple[Dict[str, Any], ...]:
    results: List[Dict[str, Any]] = []

    params = {
        'KeyConditionExpression': Key('hash_key').eq(hash_key),
    }

    if range_key:
        params['KeyConditionExpression'] &= \
            Key('range_key').begins_with(range_key)

    if attributes_to_get:
        params['AttributesToGet'] = attributes_to_get

    async with _table() as table:
        result = await table.query(**params)
        results.extend(result['Items'])

        while 'LastEvaluatedKey' in result:
            params['LastEvaluatedKey'] = result['LastEvaluatedKey']

            result = await table.query(**params)
            results.extend(result['Items'])

    for result in results:
        result.update({'hash_key': deserialize_key(result['hash_key'])})
        if 'hash_key' in result:
            result.update({'range_key': deserialize_key(result['range_key'])})

    return tuple(results)


@tracers.function.trace()
async def put(requests: Tuple[Request, ...]) -> bool:
    success: List[bool] = []

    async with _table() as table:
        for request in requests:
            if request.expires_in:
                request.expression_attribute_names['#ttl'] = 'ttl'
                request.expression_attribute_values[':ttl'] = \
                    int(time.time()) + request.expires_in
                if request.update_expression:
                    request.update_expression['SET'].add('#ttl = :ttl')
                else:
                    request.update_expression['SET'] = {'#ttl = :ttl'}
            else:
                request.expression_attribute_names.pop('#ttl', None)
                request.expression_attribute_values.pop(':ttl', None)
                if request.update_expression:
                    request.update_expression['SET'].discard('#ttl = :ttl')

            try:
                response = await table.update_item(
                    Key={
                        'hash_key': request.hash_key,
                        'range_key': request.range_key,
                    },
                    **{
                        condition_name: condition_value
                        for condition_name, condition_value in [
                            ('ConditionExpression',
                                request.condition_expression),
                            ('ExpressionAttributeNames',
                                request.expression_attribute_names),
                            ('ExpressionAttributeValues',
                                request.expression_attribute_values),
                            ('UpdateExpression',
                                ', '.join(
                                    f'{operation} {statement}'
                                    for operation, statements in
                                    request.update_expression.items()
                                    for statement in [', '.join(statements)]
                                )),
                        ]
                        if condition_value
                    },
                )
                success.append(
                    response['ResponseMetadata']['HTTPStatusCode'] == 200
                )
            except botocore.exceptions.ClientError as exception:
                if 'ConditionalCheckFailedException' in str(exception):
                    success.append(request.allow_condition_failure)
                else:
                    success.append(False)

    return all(success)


@tracers.function.trace()
@contextlib.asynccontextmanager
async def _table() -> aioboto3.dynamodb.table.TableResource:
    async with aioboto3.resource(**CONFIG) as resource:
        yield await resource.Table('main')
