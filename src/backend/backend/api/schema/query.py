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

# Pylint config
# pylint: disable=too-few-public-methods


class Query(graphene.ObjectType):  # type: ignore
    transactions = graphene.List(backend.api.schema.types.Transaction)

    @tracers.function.trace()
    async def resolve_transactions(
        self,
        _: Any,
    ) -> Tuple[backend.api.schema.types.Transaction, ...]:
        return ()
