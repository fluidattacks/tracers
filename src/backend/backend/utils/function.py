# Standard library
import inspect
from typing import (
    Any,
    Callable,
)

# Third party libraries
import tracers.function

# Local libraries
import backend.utils.aio


@tracers.function.trace()
@backend.utils.aio.to_async
def get_bound_arguments(
    function: Callable[..., Any],
    *args: Any,
    **kwargs: Any,
) -> inspect.BoundArguments:
    return inspect.signature(function).bind(*args, **kwargs).arguments
