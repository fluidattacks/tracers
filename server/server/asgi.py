# Standard library
import time
from typing import (
    Any,
    Callable,
    Coroutine,
    Dict,
)
# Third party libraries
import graphene
from graphql.execution.executors.asyncio import AsyncioExecutor
from starlette.applications import Starlette
from starlette.graphql import GraphQLApp
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.routing import Mount, Route
from starlette.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates
import tracers.daemon
import tracers.function

# Local libraries
import server.api.schema.mutation
import server.api.schema.query
import server.authc
import server.utils.aio

# Implementation
TEMPLATING_ENGINE = Jinja2Templates(
    directory='templates',
)


def render_template(
    *,
    context: Dict[str, Any],
    template: str,
) -> Callable[[Request], Coroutine[Any, Any, Response]]:

    @tracers.function.trace(overridden_function=render_template)
    async def render(request: Request) -> Response:
        return TEMPLATING_ENGINE.TemplateResponse(
            name=template,
            context=dict(request=request, **context),
        )

    return render


SERVER = Starlette(
    middleware = [
        Middleware(
            cls=server.authc.AuthenticationMidleware,
            authentication_path='/authenticate',
            authentication_required_paths=(
                '/api',
            ),
        ),
    ],
    routes=[
        Route(
            endpoint=render_template(
                context={},
                template='index.html',
            ),
            path='/',
        ),
        Route(
            endpoint=GraphQLApp(
                executor_class=AsyncioExecutor,
                graphiql=True,
                schema=graphene.Schema(
                    mutation=server.api.schema.mutation.Mutation,
                    query=server.api.schema.query.Query,
                ),
            ),
            path='/api',
        ),
        Mount(
            app=StaticFiles(
                directory='../static',
            ),
            name='static',
            path='/static',
        ),
    ],
)

tracers.daemon.start_daemon()
tracers.function.call(time.sleep, 0)
