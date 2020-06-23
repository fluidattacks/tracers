# Standard library
from typing import (
    Any,
    List,
)

# Third party libraries
import graphene

# Local libraries
import backend.api.schema.types
import backend.domain.transaction
import backend.utils.apm


class TransactionInput(graphene.InputObjectType):
    initiator = graphene.String()
    stack = backend.api.schema.types.JSONString()
    stdout = graphene.String()
    tenant_id = graphene.ID()
    total_time = graphene.Decimal()


class PutTransaction(graphene.Mutation):  # type: ignore
    class Arguments:
        transactions = graphene.List(TransactionInput)

    success = graphene.Boolean()

    @backend.utils.apm.trace()
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
