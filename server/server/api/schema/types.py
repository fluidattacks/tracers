# Standard library
from datetime import (
    datetime,
)
from decimal import (
    Decimal,
)
import json
from typing import (
    Any,
)

# Third party libraries
import dateutil.parser
import graphene
import graphql.language.ast

# Local libraries
import server.config

# Pylint config
# pylint: disable=too-few-public-methods


class DateTime(graphene.Scalar):  # type: ignore

    @staticmethod
    def serialize(data: Any) -> str:
        if not isinstance(data, datetime):
            data = dateutil.parser.parse(data)

        return str(data.isoformat())

    @staticmethod
    def parse_literal(node: object) -> Any:
        if isinstance(node, graphql.language.ast.StringValue):
            return DateTime.parse_value(node.value)

        return None

    @staticmethod
    def parse_value(value: str) -> Any:
        return dateutil.parser.parse(value)


class JSONString(graphene.Scalar):  # type: ignore

    @staticmethod
    def serialize(data: object) -> str:
        def cast(obj: object) -> object:
            casted_obj: Any

            if isinstance(obj, Decimal):
                casted_obj = str(obj)
            elif isinstance(obj, (list, set, tuple)):
                casted_obj = tuple(map(cast, obj))
            elif isinstance(obj, dict):
                casted_obj = dict(zip(obj, map(cast, obj.values())))
            else:
                casted_obj = obj

            return casted_obj

        return json.dumps(cast(data))

    @staticmethod
    def parse_literal(node: object) -> Any:
        if isinstance(node, graphql.language.ast.StringValue):
            return JSONString.parse_value(node.value)

        return None

    @staticmethod
    def parse_value(value: str) -> Any:
        return json.loads(value, parse_float=Decimal)


class TransactionInput(graphene.InputObjectType):  # type: ignore
    initiator = graphene.String()
    stack = JSONString()
    total_time = graphene.Decimal()


class Transaction(graphene.ObjectType):  # type: ignore
    initiator = graphene.String()
    max_stack = JSONString()
    max_total_time = graphene.Decimal()
    min_stack = JSONString()
    min_total_time = graphene.Decimal()
    stamp = DateTime()


TRANSACTION_INTERVAL = graphene.Enum('TransactionInterval', [
    (f'INTERVAL_{interval}', interval)
    for interval in server.config.MEASURE_INTERVALS
])
