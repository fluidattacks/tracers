# Standard library
import asyncio
import contextlib
from contextvars import (
    ContextVar,
    Token,
)
from decimal import Decimal
import json
import threading
import time
from typing import (
    Any,
    Callable,
    Iterator,
    Type,
)

# Local libraries
from tracers.containers import (
    DaemonResult,
    Frame,
    LoopSnapshot,
)
from tracers.contextvars import (
    LOGGER,
)


@contextlib.contextmanager
def condition() -> Iterator[threading.Event]:
    instance: threading.Event = threading.Event()
    try:
        yield instance
    finally:
        instance.clear()


def delta(start_timestamp: float, end_timestamp: float) -> float:
    return end_timestamp - start_timestamp


def divide(
    *,
    numerator: float,
    denominator: float,
    on_zero_denominator: float,
) -> float:
    return \
        on_zero_denominator if denominator == 0.0 else numerator / denominator


def get_function_id(function: Callable[..., Any]) -> str:
    # Adding decorators to a function modify its metadata
    #   Fortunately functools' wrapped functions keep a reference to the parent
    while hasattr(function, '__wrapped__'):
        function = getattr(function, '__wrapped__')

    module: str = function.__module__
    name: str = function.__name__
    prefix = 'async ' * asyncio.iscoroutinefunction(function)

    if module not in {'__main__'}:
        return f'{prefix}{module}.{name}'

    return f'{prefix}{name}'


def get_monotonic_time() -> float:
    return time.clock_gettime(time.CLOCK_MONOTONIC)


@contextlib.contextmanager
def increase_counter(contextvar: ContextVar[int]) -> Iterator[None]:
    token: Token[int] = contextvar.set(contextvar.get() + 1)
    try:
        yield
    finally:
        contextvar.reset(token)


def json_dumps(element: object) -> str:

    def cast(obj: Any) -> Any:
        if isinstance(obj, (DaemonResult, Frame, LoopSnapshot)):
            casted_obj: Any = dict(zip(obj._fields, cast(tuple(obj))))
        elif isinstance(obj, (list, set, tuple)):
            casted_obj = list(map(cast, obj))
        elif isinstance(obj, Decimal):
            casted_obj = float(obj)
        else:
            casted_obj = obj

        return casted_obj

    return json.dumps(cast(element))


def log(*parts: str, level: str = 'info') -> None:
    logger = LOGGER.get()
    if logger:
        getattr(logger, level)(' '.join(parts))


def on_error(
    *,
    of_type: Type[Exception],
    return_value: Any,
) -> Callable[..., Any]:

    def decorator(function: Callable[..., Any]) -> Callable[..., Any]:

        def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                value = function(*args, **kwargs)
            except of_type:
                value = return_value

            return value

        return wrapper

    return decorator
