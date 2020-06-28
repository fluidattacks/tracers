# Standard library
from typing import (
    Any,
    Tuple,
)

# Third party libraries
import graphene

# Local libraries
import backend.api.schema.types
import backend.utils.apm


class Transaction(graphene.ObjectType):
    initiator = graphene.String()
    stack = backend.api.schema.types.JSONString()
    tenant_id = graphene.ID()
    total_time = graphene.Decimal()


class Query(graphene.ObjectType):  # type: ignore
    transactions = graphene.List(Transaction)

    @backend.utils.apm.trace()
    async def resolve_transactions(
        self,
        info: Any,
    ) -> Tuple[Transaction, ...]:
        return ()
