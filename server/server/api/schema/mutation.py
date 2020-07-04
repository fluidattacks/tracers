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
import server.authc.claims
import server.domain.system

# Pylint config
# pylint: disable=too-few-public-methods


class PutSystem(graphene.Mutation):  # type: ignore
    class Arguments:
        system_id = graphene.String(required=True)

    success = graphene.Boolean()

    @tracers.function.trace()
    @server.authc.claims.verify  # type: ignore
    async def mutate(
        self,
        info: graphql.execution.base.ResolveInfo,
        system_id: str,
    ) -> 'PutSystem':
        success = await server.domain.system.put_system(
            claims=getattr(info, 'context')['authc'],
            system_id=system_id,
        )

        return PutSystem(
            success=success,
        )


class PutTransactions(graphene.Mutation):  # type: ignore
    class Arguments:
        system_id = graphene.String(required=True)
        transactions = graphene.List(
            server.api.schema.types.TransactionInput,
            required=True,
        )

    success = graphene.Boolean()

    @tracers.function.trace()
    @server.authc.claims.verify  # type: ignore
    async def mutate(
        self,
        info: graphql.execution.base.ResolveInfo,
        system_id: str,
        transactions: Tuple[server.api.schema.types.TransactionInput, ...],
    ) -> 'PutTransactions':
        success = await server.domain.system.put_transactions(
            claims=getattr(info, 'context')['authc'],
            system_id=system_id,
            transactions=transactions,
        )

        return PutTransactions(
            success=success,
        )


class Mutation(graphene.ObjectType):  # type: ignore
    put_system = PutSystem.Field()
    put_transactions = PutTransactions.Field()
