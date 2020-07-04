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
import backend.authc.claims
import backend.domain.system

# Pylint config
# pylint: disable=too-few-public-methods


class PutSystem(graphene.Mutation):  # type: ignore
    class Arguments:
        system_id = graphene.String(required=True)

    success = graphene.Boolean()

    @tracers.function.trace()
    @backend.authc.claims.verify  # type: ignore
    async def mutate(
        self,
        info: graphql.execution.base.ResolveInfo,
        system_id: str,
    ) -> 'PutSystem':
        success = await backend.domain.system.put_system(
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
            backend.api.schema.types.TransactionInput,
            required=True,
        )

    success = graphene.Boolean()

    @tracers.function.trace()
    @backend.authc.claims.verify  # type: ignore
    async def mutate(
        self,
        info: graphql.execution.base.ResolveInfo,
        system_id: str,
        transactions: Tuple[backend.api.schema.types.TransactionInput, ...],
    ) -> 'PutTransactions':
        success = await backend.domain.system.put_transactions(
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
