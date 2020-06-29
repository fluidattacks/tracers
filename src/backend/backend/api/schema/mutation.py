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
import backend.domain.transaction

# Pylint config
# pylint: disable=too-few-public-methods


class TransactionInput(graphene.InputObjectType):  # type: ignore
    initiator = graphene.String()
    stack = backend.api.schema.types.JSONString()
    tenant_id = graphene.ID()
    total_time = graphene.Decimal()


class PutTransaction(graphene.Mutation):  # type: ignore
    class Arguments:
        transactions = graphene.List(TransactionInput)

    success = graphene.Boolean()

    @tracers.function.trace()
    async def mutate(
        self,
        _: Any,
        transactions: Tuple[TransactionInput, ...],
    ) -> 'PutTransaction':
        success = await backend.domain.transaction.put(
            transactions=transactions,
        )

        return PutTransaction(
            success=success,
        )


class Mutation(graphene.ObjectType):  # type: ignore
    put_transaction = PutTransaction.Field()
