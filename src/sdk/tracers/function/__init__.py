# Standard library
import asyncio
import contextlib
import contextvars
import functools
import time
from typing import (
    Any,
    Callable,
    List,
    Optional,
    Tuple,
)

# Local libraries
from tracers.analyzers import (
    analyze_loop_snapshots,
    analyze_stack,
)
from tracers.constants import (
    LOOP_CHECK_INTERVAL,
)
from tracers.containers import (
    Frame,
    LoopSnapshot,
)
from tracers.contextvars import (
    LEVEL,
    STACK,
    TRACING,
)
from tracers.utils import (
    delta,
    divide,
    get_function_id,
    increase_counter,
)

# Types
FunctionWrapper = Callable[[Callable[..., Any]], Callable[..., Any]]


def measure_loop_skew(snapshots: List[LoopSnapshot], clock_id: int) -> None:

    def callback_handler(
        wanted_tick_duration: float,
        start_timestamp: float,
    ) -> None:
        real_tick_duration: float = \
            delta(start_timestamp, time.clock_gettime(clock_id))

        snapshots.append(LoopSnapshot(
            block_duration_ratio=divide(
                numerator=real_tick_duration,
                denominator=wanted_tick_duration,
                on_zero_denominator=1.0,
            ),
            real_tick_duration=real_tick_duration,
            timestamp=start_timestamp,
            wanted_tick_duration=wanted_tick_duration,
        ))

        if LEVEL.get() == 1:
            schedule_callback(wanted_tick_duration)

    def schedule_callback(wanted_tick_duration: float) -> None:
        with contextlib.suppress(RuntimeError):
            callback_handler_args: Tuple[float, float] = (
                wanted_tick_duration, time.clock_gettime(clock_id),
            )

            loop = asyncio.get_running_loop()
            loop.call_later(
                wanted_tick_duration,
                callback_handler,
                *callback_handler_args,
            )

    schedule_callback(LOOP_CHECK_INTERVAL)


def record(
    clock_id: int,
    event: str,
    function: Callable[..., Any],
    function_name: str = '',
) -> None:
    STACK.set(STACK.get() + (Frame(
        event=event,
        function=function_name or get_function_id(function),
        level=LEVEL.get(),
        timestamp=time.clock_gettime(clock_id),
    ),))


def _get_wrapper(  # noqa: MC001
    *,
    clock_id: int = time.CLOCK_MONOTONIC,
    do_trace: bool = True,
    function_name: str = '',
) -> FunctionWrapper:

    def decorator(function: Callable[..., Any]) -> Callable[..., Any]:

        if asyncio.iscoroutinefunction(function):

            @functools.wraps(function)
            async def isolated_wrapper(*args: Any, **kwargs: Any) -> Any:
                if do_trace and TRACING.get():
                    with increase_counter(LEVEL):
                        if LEVEL.get() == 1:
                            snapshots: List[LoopSnapshot] = []
                            measure_loop_skew(snapshots, clock_id)

                        record(clock_id, 'call', function, function_name)
                        result = await function(*args, **kwargs)
                        record(clock_id, 'return', function, function_name)

                        if LEVEL.get() == 1:
                            analyze_stack()
                            analyze_loop_snapshots(tuple(snapshots))
                else:
                    # Disable downstream tracers
                    TRACING.set(False)

                    # No overhead is introduced!
                    result = await function(*args, **kwargs)

                return result

        elif callable(function):

            @functools.wraps(function)
            def isolated_wrapper(*args: Any, **kwargs: Any) -> Any:

                @functools.wraps(function)
                def wrapper(*args: Any, **kwargs: Any) -> Any:
                    if do_trace and TRACING.get():
                        with increase_counter(LEVEL):
                            record(clock_id, 'call', function, function_name)
                            result = function(*args, **kwargs)
                            record(clock_id, 'return', function, function_name)

                            if LEVEL.get() == 1:
                                analyze_stack()
                    else:
                        # Disable downstream tracers
                        TRACING.set(False)

                        # No overhead is introduced!
                        result = function(*args, **kwargs)

                    return result

                if LEVEL.get() == 0:
                    result = contextvars.copy_context().run(
                        wrapper, *args, **kwargs
                    )
                else:
                    result = wrapper(*args, **kwargs)

                return result

        else:

            # We were not able to wrap this object
            raise TypeError(
                f'Excpected callable or coroutine function, '
                f'got: {type(function)}'
            )

        return isolated_wrapper

    return decorator


def trace_process(
    *,
    do_trace: bool = True,
    function_name: str = '',
) -> FunctionWrapper:
    return _get_wrapper(
        clock_id=time.CLOCK_PROCESS_CPUTIME_ID,
        do_trace=do_trace,
        function_name=function_name,
    )


def trace_thread(
    *,
    do_trace: bool = True,
    function_name: str = '',
) -> FunctionWrapper:
    return _get_wrapper(
        clock_id=time.CLOCK_THREAD_CPUTIME_ID,
        do_trace=do_trace,
        function_name=function_name,
    )


def trace_monotonic(
    *,
    do_trace: bool = True,
    function_name: str = '',
) -> FunctionWrapper:
    return _get_wrapper(
        clock_id=time.CLOCK_MONOTONIC,
        do_trace=do_trace,
        function_name=function_name,
    )


def trace(
    function: Optional[Callable[..., Any]] = None,
    *,
    do_trace: bool = True,
    function_name: str = '',
) -> FunctionWrapper:
    wrapper: FunctionWrapper = trace_monotonic(
        do_trace=do_trace,
        function_name=function_name,
    )

    if function:
        return wrapper(function)

    return wrapper
