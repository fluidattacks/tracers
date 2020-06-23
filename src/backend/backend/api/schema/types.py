# Standard library
from decimal import (
    Decimal,
)
import json

# Third party libraries
import graphene
import graphql.language.ast


class JSONString(graphene.Scalar):

    @staticmethod
    def serialize(dt):
        return json.dumps(dt,)

    @staticmethod
    def parse_literal(node):
        if isinstance(node, graphql.language.ast.StringValue):
            return json.loads(node.value, parse_float=Decimal)

    @staticmethod
    def parse_value(value):
        return json.loads(value, parse_float=Decimal)
