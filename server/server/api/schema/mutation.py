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
import server.domain.user

# Pylint config
# pylint: disable=too-few-public-methods


class PutSystem(graphene.Mutation):  # type: ignore
    class Arguments:
        system_id = graphene.String(required=True)

    success = graphene.Boolean()

    @tracers.function.trace()
    async def mutate(
        self,
        info: graphql.execution.base.ResolveInfo,
        system_id: str,
    ) -> 'PutSystem':
        success = await server.domain.system.put_tenant__system(
            claims=info.context['request'].state.verified_claims,
            system_id=system_id,
        )

        return PutSystem(
            success=success,
        )


class PutSystemTransactions(graphene.Mutation):  # type: ignore
    class Arguments:
        system_id = graphene.String(required=True)
        transactions = graphene.List(
            server.api.schema.types.TransactionInput,
            required=True,
        )

    success = graphene.Boolean()

    @tracers.function.trace()
    async def mutate(
        self,
        info: graphql.execution.base.ResolveInfo,
        system_id: str,
        transactions: Tuple[server.api.schema.types.TransactionInput, ...],
    ) -> 'PutSystemTransactions':
        success = await server.domain.system.put_system_measure__transactions(
            claims=info.context['request'].state.verified_claims,
            system_id=system_id,
            transactions=transactions,
        )

        return PutSystemTransactions(
            success=success,
        )


class PutUser(graphene.Mutation):  # type: ignore

    class Arguments:
        user_id = graphene.String(required=True)
        user_secret = graphene.String(required=True)

    success = graphene.Boolean()

    @tracers.function.trace()
    async def mutate(
        self,
        _: graphql.execution.base.ResolveInfo,
        user_id: str,
        user_secret: str,
    ) -> 'PutUser':
        success = await server.domain.user.put_user_credential(
            user_id=user_id,
            user_secret=user_secret,
        )

        return PutUser(
            success=success,
        )


class Mutation(graphene.ObjectType):  # type: ignore
    put_system = PutSystem.Field()
    put_system_transactions = PutSystemTransactions.Field()
    put_user = PutUser.Field()
