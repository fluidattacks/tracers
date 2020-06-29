# Standard library
from decimal import (
    Decimal,
)
import json
from typing import (
    Any,
)

# Third party libraries
import graphene
import graphql.language.ast


class JSONString(graphene.Scalar):  # type: ignore

    @staticmethod
    def serialize(data: object) -> str:
        return json.dumps(data)

    @staticmethod
    def parse_literal(node: object) -> Any:
        if isinstance(node, graphql.language.ast.StringValue):
            return json.loads(node.value, parse_float=Decimal)

        return None

    @staticmethod
    def parse_value(value: str) -> Any:
        return json.loads(value, parse_float=Decimal)
