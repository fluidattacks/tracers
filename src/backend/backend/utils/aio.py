# Standard library
import asyncio
from concurrent.futures import (
    ProcessPoolExecutor,
    ThreadPoolExecutor,
)
import functools
from multiprocessing import cpu_count
from typing import (
    Any,
    Tuple,
    Callable,
    Union,
)

# Third party libraries
import tracers.function

# Executors
PROCESSOR = ProcessPoolExecutor(max_workers=cpu_count() - 1)
THREADER = ThreadPoolExecutor(max_workers=cpu_count() - 1)


@tracers.function.trace()
async def _ensure(
    executor: Union[ProcessPoolExecutor, ThreadPoolExecutor],
    functions: Tuple[Callable[..., Any], ...],
) -> Any:
    loop = asyncio.get_running_loop()

    return await materialize(tuple(
        loop.run_in_executor(executor, functions) for functions in functions
    ))


@tracers.function.trace()
async def ensure_cpu_bound(
    function: Callable[..., Any],
    *args: Any,
    **kwargs: Any,
) -> Any:
    return await _ensure(PROCESSOR, [
        functools.partial(function, *args, **kwargs)
    ])


@tracers.function.trace()
async def ensure_io_bound(
    function: Callable[..., Any],
    *args: Any,
    **kwargs: Any,
) -> Any:
    return await _ensure(THREADER, [
        functools.partial(function, *args, **kwargs)
    ])


@tracers.function.trace()
async def ensure_many_cpu_bound(
    functions: Tuple[Callable[..., Any], ...],
) -> Any:
    return await _ensure(PROCESSOR, functions)


@tracers.function.trace()
async def ensure_many_io_bound(
    functions: Tuple[Callable[..., Any], ...],
) -> Any:
    return await _ensure(THREADER, functions)



@tracers.function.trace()
async def materialize(obj: object) -> object:
    materialized_obj: object

    if isinstance(obj, (dict,)):
        materialized_obj = \
            dict(zip(obj, await materialize(tuple(obj.values()))))
    elif isinstance(obj, (list, tuple)):
        materialized_obj = \
            await asyncio.gather(*tuple(map(asyncio.create_task, obj)))
    else:
        raise ValueError(f'Not implemented for type: {type(obj)}')

    return materialized_obj


async def _wrap_function(
    ensurer: Callable[[Callable[..., Any], ...], Any],
) -> Callable[..., Any]:

    async def decorator(function: Callable[..., Any]) -> Callable[..., Any]:

        @functools.wraps(function)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            return await ensurer(function, *args, **kwargs)

        return wrapper

    return decorator


async def wrap_cpu_bound(function: Callable[..., Any]) -> Callable[..., Any]:
    return _wrap_function(ensure_cpu_bound)(function)


async def wrap_io_bound(function: Callable[..., Any]) -> Callable[..., Any]:
    return _wrap_function(ensure_io_bound)(function)
