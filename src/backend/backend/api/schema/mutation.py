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
import backend.domain.transaction

# Pylint config
# pylint: disable=too-few-public-methods


class PutTransaction(graphene.Mutation):  # type: ignore
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
    ) -> 'PutTransaction':
        success = await backend.domain.transaction.put_many(
            claims=getattr(info, 'context')['authc'],
            system_id=system_id,
            transactions=transactions,
        )

        return PutTransaction(
            success=success,
        )


class Mutation(graphene.ObjectType):  # type: ignore
    put_transaction = PutTransaction.Field()
