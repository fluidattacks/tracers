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
        app=graphene.String(required=True),
        env=graphene.String(required=True),
        interval=backend.api.schema.types.TRANSACTION_INTERVAL(required=True),
    )

    @tracers.function.trace()
    @backend.authc.claims.verify  # type: ignore
    async def resolve_transactions(
        self,
        info: graphql.execution.base.ResolveInfo,
        *,
        app: str,
        env: str,
        interval: int,
    ) -> Tuple[backend.api.schema.types.Transaction, ...]:
        return await backend.domain.transaction.get(
            app=app,
            claims=getattr(info, 'context')['authc'],
            env=env,
            interval=interval,
        )
