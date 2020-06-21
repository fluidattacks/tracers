# Standard library
import asyncio
import contextlib
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
    LOOP_SNAPSHOTS,
    reset_all as reset_all_contextvars,
    STACK,
    TRACING,
)
from tracers.utils import (
    divide,
    get_function_id,
    increase_counter,
)

# Types
FunctionWrapper = Callable[[Callable[..., Any]], Callable[..., Any]]


def measure_loop_skew(clock_id: int) -> None:

    def callback_handler(
        wanted_tick_duration: float,
        start_timestamp: float,
    ) -> None:
        timestamp: float = time.clock_gettime(clock_id)
        real_tick_duration: float = timestamp - start_timestamp
        block_duration_ratio: float = divide(
            numerator=real_tick_duration,
            denominator=wanted_tick_duration,
            on_zero_denominator=1.0,
        )

        LOOP_SNAPSHOTS.get().append(LoopSnapshot(
            block_duration_ratio=block_duration_ratio,
            wanted_tick_duration=wanted_tick_duration,
            real_tick_duration=real_tick_duration,
            timestamp=start_timestamp,
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
                *callback_handler_args
            )

    if LEVEL.get() == 1:
        schedule_callback(LOOP_CHECK_INTERVAL)


def record_event(
    clock_id: int,
    event: str,
    function: Callable[..., Any],
    function_name: str = '',
) -> None:
    STACK.get().append(Frame(
        event=event,
        function=function_name or get_function_id(function),
        level=LEVEL.get(),
        timestamp=time.clock_gettime(clock_id),
    ))


def _get_wrapper(  # noqa: MC001
    *,
    clock_id: int = time.CLOCK_MONOTONIC,
    do_trace: bool = True,
    function_name: str = '',
    loop_snapshots_analyzer: Callable[[List[LoopSnapshot]], None] =
    analyze_loop_snapshots,
    stack_analyzer: Callable[[List[Frame]], None] =
    analyze_stack,
) -> FunctionWrapper:

    def decorator(function: Callable[..., Any]) -> Callable[..., Any]:

        if not do_trace or not TRACING.get():

            # No overhead is introduced
            wrapper = function

            # Any downstream tracer is also disabled
            TRACING.set(False)

        elif asyncio.iscoroutinefunction(function):

            @functools.wraps(function)
            async def wrapper(*args: Any, **kwargs: Any) -> Any:
                if LEVEL.get() == 0:
                    reset_all_contextvars()

                with increase_counter(LEVEL):
                    measure_loop_skew(clock_id)
                    record_event(clock_id, 'call', function, function_name)
                    result = await function(*args, **kwargs)
                    record_event(clock_id, 'return', function, function_name)

                if LEVEL.get() == 0:
                    stack_analyzer(STACK.get())
                    loop_snapshots_analyzer(LOOP_SNAPSHOTS.get())

                return result

        elif callable(function):

            @functools.wraps(function)
            def wrapper(*args: Any, **kwargs: Any) -> Any:
                if LEVEL.get() == 0:
                    reset_all_contextvars()

                with increase_counter(LEVEL):
                    record_event(clock_id, 'call', function, function_name)
                    result = function(*args, **kwargs)
                    record_event(clock_id, 'return', function, function_name)

                if LEVEL.get() == 0:
                    stack_analyzer(STACK.get())

                return result

        else:

            # We were not able to wrap this object
            wrapper = function

        return wrapper

    return decorator


def trace_process(
    *,
    do_trace: bool = True,
    function_name: str = '',
    loop_snapshots_analyzer: Callable[[List[LoopSnapshot]], None] =
    analyze_loop_snapshots,
    stack_analyzer: Callable[[List[Frame]], None] =
    analyze_stack,
) -> FunctionWrapper:
    return _get_wrapper(
        clock_id=time.CLOCK_PROCESS_CPUTIME_ID,
        do_trace=do_trace,
        function_name=function_name,
        loop_snapshots_analyzer=loop_snapshots_analyzer,
        stack_analyzer=stack_analyzer,
    )


def trace_thread(
    *,
    do_trace: bool = True,
    function_name: str = '',
    loop_snapshots_analyzer: Callable[[List[LoopSnapshot]], None] =
    analyze_loop_snapshots,
    stack_analyzer: Callable[[List[Frame]], None] =
    analyze_stack,
) -> FunctionWrapper:
    return _get_wrapper(
        clock_id=time.CLOCK_THREAD_CPUTIME_ID,
        do_trace=do_trace,
        function_name=function_name,
        loop_snapshots_analyzer=loop_snapshots_analyzer,
        stack_analyzer=stack_analyzer,
    )


def trace_monotonic(
    *,
    do_trace: bool = True,
    function_name: str = '',
    loop_snapshots_analyzer: Callable[[List[LoopSnapshot]], None] =
    analyze_loop_snapshots,
    stack_analyzer: Callable[[List[Frame]], None] =
    analyze_stack,
) -> FunctionWrapper:
    return _get_wrapper(
        clock_id=time.CLOCK_MONOTONIC,
        do_trace=do_trace,
        function_name=function_name,
        loop_snapshots_analyzer=loop_snapshots_analyzer,
        stack_analyzer=stack_analyzer,
    )


def trace(
    function: Optional[Callable[..., Any]] = None,
    *,
    do_trace: bool = True,
    function_name: str = '',
    loop_snapshots_analyzer: Callable[[List[LoopSnapshot]], None] =
    analyze_loop_snapshots,
    stack_analyzer: Callable[[List[Frame]], None] =
    analyze_stack,
) -> FunctionWrapper:
    wrapper: FunctionWrapper = trace_monotonic(
        do_trace=do_trace,
        function_name=function_name,
        loop_snapshots_analyzer=loop_snapshots_analyzer,
        stack_analyzer=stack_analyzer,
    )

    if function:
        return wrapper(function)

    return wrapper
