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
import backend.utils.aio

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
@backend.utils.aio.to_async  # type: ignore
def build_key(parameters: Dict[str, str]) -> str:
    if not parameters:
        raise ValueError('Empty parameters')

    if not all(
        isinstance(obj, str)
        for arguments in parameters.items()
        for obj in arguments
    ):
        raise TypeError('Expected Dict[str, str]')

    return '/'.join(
        f'{attribute_name.encode().hex()}:{attribute_value.encode().hex()}'
        for attribute_name, attribute_value in parameters.items()
    )


@tracers.function.trace()
async def query(
    *,
    hash_key: str,
    range_key: Optional[str] = None,
    attributes_to_get: Optional[Tuple[str, ...]] = None,
) -> Tuple[object, ...]:
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
                request.update_expression['SET'].add('#ttl = :ttl')
            else:
                request.expression_attribute_names.pop('#ttl', None)
                request.expression_attribute_values.pop(':ttl', None)
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
