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

# Local libraries
from backend.typing import (
    T,
    V,
)

# Executors
PROCESSOR = ProcessPoolExecutor(max_workers=cpu_count() - 1)
THREADER = ThreadPoolExecutor(max_workers=cpu_count() - 1)


@tracers.function.trace()
async def _ensure(
    executor: Union[ProcessPoolExecutor, ThreadPoolExecutor],
    functions: Tuple[Callable[..., T], ...],
) -> Tuple[T, ...]:
    loop = asyncio.get_running_loop()

    return await materialize(tuple(
        loop.run_in_executor(executor, function) for function in functions
    ))


@tracers.function.trace()
async def ensure_cpu_bound(
    function: Callable[..., Any],
    *args: Any,
    **kwargs: Any,
) -> Any:
    results = await _ensure(PROCESSOR, [
        functools.partial(function, *args, **kwargs)
    ])

    return results[0]


@tracers.function.trace()
async def ensure_io_bound(
    function: Callable[..., T],
    *args: Any,
    **kwargs: Any,
) -> T:
    results = await _ensure(THREADER, [
        functools.partial(function, *args, **kwargs)
    ])

    return results[0]


@tracers.function.trace()
async def ensure_many_cpu_bound(
    functions: Tuple[Callable[[], Any], ...],
) -> Any:
    return await _ensure(PROCESSOR, functions)


@tracers.function.trace()
async def ensure_many_io_bound(
    functions: Tuple[Callable[[], Any], ...],
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
            await asyncio.gather(*tuple(
                elem
                if isinstance(elem, asyncio.Future)
                else asyncio.create_task(elem)
                for elem in obj
            ))
    else:
        raise ValueError(f'Not implemented for type: {type(obj)}')

    return materialized_obj


def to_async(function: Callable[..., T]) -> Callable[..., T]:

    @tracers.function.trace(function_name='to_async')
    @functools.wraps(function)
    async def wrapper(*args: str, **kwargs: Any) -> T:
        result = await ensure_io_bound(function, *args, **kwargs)

        return result

    return wrapper
