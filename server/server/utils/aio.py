# Standard library
import asyncio
import collections.abc
from concurrent.futures import (
    ThreadPoolExecutor,
)
import functools
from multiprocessing import cpu_count
from typing import (
    Any,
    Awaitable,
    cast,
    Tuple,
    Callable,
    Union,
)

# Third party libraries
import tracers.function

# Local libraries
from server.typing import (
    T,
)

# Executors
THREADER = ThreadPoolExecutor(max_workers=2)


async def unblock(
    function: Callable[..., T],
    *args: Any,
    **kwargs: Any,
) -> T:
    return await asyncio.get_running_loop().run_in_executor(
        THREADER, functools.partial(function, *args, **kwargs),
    )


@tracers.function.trace()
async def unblock_many(
    functions: Tuple[Callable[[], Any], ...],
) -> Any:
    loop = asyncio.get_running_loop()

    return await materialize((
        loop.run_in_executor(THREADER, function) for function in functions
    ))


@tracers.function.trace()
async def materialize(obj: object) -> object:
    materialized_obj: object

    # Please use abstract base classes:
    #   https://docs.python.org/3/glossary.html#term-abstract-base-class
    #
    # Pick them up here according to the needed interface:
    #   https://docs.python.org/3/library/collections.abc.html
    #

    if isinstance(obj, collections.abc.Mapping):
        materialized_obj = dict(zip(
            obj,
            await materialize(obj.values()),
        ))
    elif isinstance(obj, collections.abc.Iterable):
        materialized_obj = [
            await awaitable for awaitable in [
                elem
                if isinstance(elem, asyncio.Future)
                else asyncio.create_task(elem)
                for elem in obj
            ]
        ]
    else:
        raise ValueError(f'Not implemented for type: {type(obj)}')

    return materialized_obj


def to_async(function: Callable[..., T]) -> Callable[..., Awaitable[T]]:

    @tracers.function.trace(overridden_function=to_async)
    @functools.wraps(function)
    async def wrapper(*args: str, **kwargs: Any) -> Any:
        return await unblock(function, *args, **kwargs)

    return cast(Callable[..., Awaitable[T]], wrapper)
