# Standard library
from collections import (
    OrderedDict,
)
import functools
import inspect
from typing import (
    Any,
    cast,
    Callable,
    NamedTuple,
)

# Third party libraries
import graphql.execution.base
import starlette.requests
import tracers.function

# Local libraries
import backend.utils.function
import backend.utils.jwt
from backend.typing import (
    T,
)


class TracersTenant(NamedTuple):
    app: str
    env: str
    tenant_id: str


def verify(function: T) -> T:

    @tracers.function.trace(function_name='verify')
    @functools.wraps(function)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        arguments = await backend.utils.function.get_bound_arguments(
            function, *args, **kwargs,
        )

        info: graphql.execution.base.ResolveInfo = arguments['info']

        request: starlette.requests.Request = info.context['request']

        _, token = request.headers['authorization'].split(' ', maxsplit=1)

        claims = await backend.utils.jwt.deserialize(token)

        info.context['authc'] = TracersTenant(**claims)

        return await function(*args, **kwargs)

    return cast(T, wrapper)
