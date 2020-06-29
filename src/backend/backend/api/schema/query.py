# Standard library
from typing import (
    Any,
    Tuple,
)

# Third party libraries
import graphene
import tracers.function

# Local libraries
import backend.api.schema.types

# Pylint config
# pylint: disable=too-few-public-methods


class Transaction(graphene.ObjectType):  # type: ignore
    initiator = graphene.String()
    stack = backend.api.schema.types.JSONString()
    tenant_id = graphene.ID()
    total_time = graphene.Decimal()


class Query(graphene.ObjectType):  # type: ignore
    transactions = graphene.List(Transaction)

    @tracers.function.trace()
    async def resolve_transactions(
        self,
        _: Any,
    ) -> Tuple[Transaction, ...]:
        return ()
