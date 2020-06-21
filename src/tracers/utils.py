# Standard library
import asyncio
from collections import deque
import contextlib
from contextvars import (
    Token,
)
import inspect
from typing import (
    Callable,
    Tuple,
)

# Third party imports
from more_itertools import iter_except


def delta(start_timestamp: float, end_timestamp: float):
    return end_timestamp - start_timestamp


def divide(
    *,
    numerator: float,
    denominator: float,
    on_zero_denominator: float,
) -> float:
    return \
        on_zero_denominator if denominator == 0.0 else numerator / denominator


def drain_queue(queue: deque) -> tuple:
    return tuple(iter_except(queue.pop, IndexError))


def get_function_id(function: Callable) -> Tuple[str, str]:
    # Adding decorators to a function modify its metadata
    #   Fortunately functools' wrapped functions keep a reference to the parent
    while hasattr(function, '__wrapped__'):
        function = getattr(function, '__wrapped__')

    signature: str = '(...)'
    with contextlib.suppress(ValueError):
        signature = str(inspect.signature(function))

    module: str = function.__module__
    name: str = function.__name__
    prefix = 'async ' * asyncio.iscoroutinefunction(function)
    signature = signature if len(signature) < 48 else '(...)'

    if module not in {'__main__'}:
        return f'{prefix}{module}.{name}', signature

    return f'{prefix}{name}', signature


@contextlib.contextmanager
def increase_counter(contextvar):
    token: Token = contextvar.set(contextvar.get() + 1)
    try:
        yield
    finally:
        contextvar.reset(token)


def log(*parts):
    print(*parts)
