# Standard library
from typing import (
    Any,
    List,
)

# Third party libraries
import graphene

# Local libraries
import backend.domain.transaction


class TransactionInput(graphene.InputObjectType):
    initiator = graphene.String()
    stack = graphene.JSONString()
    stdout = graphene.String()
    tenant_id = graphene.ID()
    total_time = graphene.Decimal()


class PutTransaction(graphene.Mutation):  # type: ignore
    class Arguments:
        transactions = graphene.List(TransactionInput)

    success = graphene.Boolean()

    async def mutate(
        self,
        info: Any,
        transactions: List[TransactionInput],
    ) -> 'PutTransaction':
        success = await backend.domain.transaction.put(
            transactions=transactions,
        )

        return PutTransaction(
            success=success,
        )


class Mutation(graphene.ObjectType):  # type: ignore
    put_transaction = PutTransaction.Field()
