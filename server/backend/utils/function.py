# Standard library
import inspect
from typing import (
    Any,
    Callable,
)

# Third party libraries
import tracers.function


@tracers.function.trace()
def get_bound_arguments(
    function: Callable[..., Any],
    *args: Any,
    **kwargs: Any,
) -> inspect.BoundArguments:
    return inspect.signature(function).bind(*args, **kwargs).arguments
