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
    NamedTuple,
)

# Local libraries
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

    def encoder(obj: Any) -> Any:
        if isinstance(obj, (set, tuple)):
            casted_obj: Any = list(map(encoder, obj))
        elif isinstance(obj, NamedTuple):
            casted_obj = dict(zip(obj._fields, encoder(tuple(obj))))
        elif isinstance(obj, Decimal):
            casted_obj = float(obj)
        else:
            casted_obj = obj

        return casted_obj

    return json.dumps(element, default=encoder)


def log(*parts: str) -> None:
    logger = LOGGER.get()
    if logger:
        logger.info(' '.join(parts))
