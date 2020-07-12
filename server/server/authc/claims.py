# Standard library
import functools
from typing import (
    Any,
    cast,
    NamedTuple,
)

# Third party libraries
import graphql.execution.base
import starlette.requests
import tracers.function

# Local libraries
import server.config
import server.utils.function
import server.utils.jwt
from server.typing import (
    T,
)


class TracersTenant(NamedTuple):
    tenant_id: str


def process(function: T) -> T:

    @tracers.function.trace(overridden_function=process)
    @functools.wraps(function)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        arguments = server.utils.function.get_bound_arguments(
            function, *args, **kwargs,
        )

        info: graphql.execution.base.ResolveInfo = arguments['info']

        request: starlette.requests.Request = info.context['request']

        request_claims: str
        if server.config.HTTP_AUTH_HEADER in request.headers:
            request_claims = request.headers[server.config.HTTP_AUTH_HEADER]
        elif server.config.HTTP_AUTH_COOKIE in request.cookies:
            request_claims = request.cookies[server.config.HTTP_AUTH_COOKIE]
        else:
            raise TypeError('Expected a Bearer token in cookie or header')

        kind, token = request_claims.split(' ', maxsplit=1)

        if kind not in ['Bearer']:
            raise TypeError('Expected a Bearer token')

        claims = server.utils.jwt.deserialize(token)

        info.context['claims'] = TracersTenant(**claims)

        return await function(*args, **kwargs)

    return cast(T, wrapper)
