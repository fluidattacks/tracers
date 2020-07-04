# Standard library
import time

# Third party libraries
import graphene
from graphql.execution.executors.asyncio import AsyncioExecutor
from starlette.applications import Starlette
from starlette.graphql import GraphQLApp
from starlette.routing import Route
import tracers.function

# Local libraries
import server.api.schema.mutation
import server.api.schema.query

SERVER = Starlette(
    routes=[
        Route('/api', GraphQLApp(
            executor_class=AsyncioExecutor,
            graphiql=True,
            schema=graphene.Schema(
                mutation=server.api.schema.mutation.Mutation,
                query=server.api.schema.query.Query,
            ),
        )),
    ],
)

tracers.function.call(time.sleep, 0)
