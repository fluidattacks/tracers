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
import server.utils.function
import server.utils.jwt
from server.typing import (
    T,
)


class TracersTenant(NamedTuple):
    tenant_id: str


def verify(function: T) -> T:

    @tracers.function.trace(overridden_function=verify)
    @functools.wraps(function)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        arguments = server.utils.function.get_bound_arguments(
            function, *args, **kwargs,
        )

        info: graphql.execution.base.ResolveInfo = arguments['info']

        request: starlette.requests.Request = info.context['request']

        _, token = request.headers['authorization'].split(' ', maxsplit=1)

        claims = server.utils.jwt.deserialize(token)

        info.context['authc'] = TracersTenant(**claims)

        return await function(*args, **kwargs)

    return cast(T, wrapper)
