# Standard library
from typing import (
    Tuple,
)

# Third party libraries
import graphene
import graphql.execution.base
import tracers.function

# Local libraries
import backend.api.schema.types

# Pylint config
# pylint: disable=too-few-public-methods


class Query(graphene.ObjectType):  # type: ignore
    transactions = graphene.Field(
        graphene.List(backend.api.schema.types.Transaction),
        interval=backend.api.schema.types.TRANSACTION_INTERVAL(required=True),
        system_id=graphene.String(required=True),
    )

    @tracers.function.trace()
    @backend.authc.claims.verify  # type: ignore
    async def resolve_transactions(
        self,
        info: graphql.execution.base.ResolveInfo,
        *,
        interval: int,
        system_id: str,
    ) -> Tuple[backend.api.schema.types.Transaction, ...]:
        return await backend.domain.transaction.get(
            claims=getattr(info, 'context')['authc'],
            interval=interval,
            system_id=system_id,
        )
