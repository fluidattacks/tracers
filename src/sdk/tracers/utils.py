# Standard library
import asyncio
import contextlib
from contextvars import (
    ContextVar,
    Token,
)
import sys
import threading
import time
from typing import (
    Any,
    Callable,
    Iterator,
)

# Local libraries
from tracers.contextvars import (
    LOGGING_TO,
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


def get_function_id(
    function: Callable[..., Any],
) -> str:
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


def log(*parts: Any) -> None:
    if LOGGING_TO.get():
        print(*parts, file=LOGGING_TO.get())


def log_stderr(*parts: Any) -> None:
    print(*parts, file=sys.stderr)
