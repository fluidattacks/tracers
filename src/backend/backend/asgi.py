# Third party libraries
import graphene
from graphql.execution.executors.asyncio import AsyncioExecutor
from starlette.applications import Starlette
from starlette.graphql import GraphQLApp
from starlette.routing import Route

# Local libraries
import backend.api.schema.mutation

SERVER = Starlette(
    routes=[
        Route('/api', GraphQLApp(
            executor_class=AsyncioExecutor,
            graphiql=True,
            schema=graphene.Schema(
                mutation=backend.api.schema.mutation.Mutation,
            ),
        )),
    ],
)
