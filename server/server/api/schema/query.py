# Standard library
from typing import (
    Tuple,
)

# Third party libraries
import graphene
import graphql.execution.base
import tracers.function

# Local libraries
import server.api.schema.types
import server.domain.system

# Pylint config
# pylint: disable=too-few-public-methods


class Query(graphene.ObjectType):  # type: ignore
    transactions = graphene.Field(
        graphene.List(server.api.schema.types.Transaction),
        interval=server.api.schema.types.TRANSACTION_INTERVAL(required=True),
        system_id=graphene.String(required=True),
    )

    @tracers.function.trace()
    @server.authc.claims.process  # type: ignore
    async def resolve_transactions(
        self,
        info: graphql.execution.base.ResolveInfo,
        *,
        interval: int,
        system_id: str,
    ) -> Tuple[server.api.schema.types.Transaction, ...]:
        return await server.domain.system.get_system_measure__transaction(
            claims=getattr(info, 'context')['claims'],
            interval=interval,
            system_id=system_id,
        )
