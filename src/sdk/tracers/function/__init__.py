# Standard library
import asyncio
import contextlib
import contextvars
import functools
import logging
import threading
from typing import (
    Any,
    Callable,
    List,
    Optional,
)

# Local libraries
from tracers.analyzers import (
    analyze_loop_snapshots,
    analyze_stack,
)
from tracers.constants import (
    LOGGER_DEFAULT,
    LOOP_CHECK_INTERVAL,
)
from tracers.containers import (
    DaemonResult,
    Frame,
    LoopSnapshot,
)
from tracers.contextvars import (
    LEVEL,
    LOGGER,
    STACK,
    TRACING,
)
from tracers.daemon import (
    send_result_to_daemon,
)
from tracers.utils import (
    condition,
    delta,
    divide,
    get_function_id,
    get_monotonic_time,
    increase_counter,
)


def measure_loop_skew(
    should_measure: threading.Event,
    snapshots: List[LoopSnapshot],
) -> None:

    def callback_handler(start_timestamp: float) -> None:
        real_tick_duration: float = \
            delta(start_timestamp, get_monotonic_time())

        snapshots.append(LoopSnapshot(
            block_duration_ratio=divide(
                numerator=real_tick_duration,
                denominator=LOOP_CHECK_INTERVAL,
                on_zero_denominator=1.0,
            ),
            real_tick_duration=real_tick_duration,
            timestamp=start_timestamp,
            wanted_tick_duration=LOOP_CHECK_INTERVAL,
        ))

        schedule_callback()

    def schedule_callback() -> None:
        if should_measure.is_set():
            with contextlib.suppress(RuntimeError):
                asyncio.get_running_loop().call_later(
                    LOOP_CHECK_INTERVAL,
                    callback_handler,
                    get_monotonic_time(),
                )

    schedule_callback()


def record_event(
    event: str,
    function: Callable[..., Any],
    function_name: str = '',
) -> None:
    STACK.set(STACK.get() + (Frame(
        event=event,
        function=function_name or get_function_id(function),
        level=LEVEL.get(),
        timestamp=get_monotonic_time(),
    ),))


def trace(  # noqa: MC0001
    *,
    enabled: bool = True,
    function_name: str = '',
    log_to: Optional[logging.Logger] = LOGGER_DEFAULT,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:

    def decorator(function: Callable[..., Any]) -> Callable[..., Any]:

        if asyncio.iscoroutinefunction(function):

            @functools.wraps(function)
            async def isolated_wrapper(*args: Any, **kwargs: Any) -> Any:

                @functools.wraps(function)
                async def wrapper(*args: Any, **kwargs: Any) -> Any:
                    if LEVEL.get() == 0:
                        LOGGER.set(log_to)

                    if enabled and TRACING.get():
                        with condition() as should_measure_loop_skew, \
                                increase_counter(LEVEL):
                            if LEVEL.get() == 1:
                                should_measure_loop_skew.set()
                                snapshots: List[LoopSnapshot] = []
                                measure_loop_skew(
                                    should_measure_loop_skew,
                                    snapshots,
                                )

                            record_event('call', function, function_name)
                            result = await function(*args, **kwargs)
                            record_event('return', function, function_name)

                            if LEVEL.get() == 1:
                                stack = STACK.get()
                                analyze_stack(stack)
                                analyze_loop_snapshots(tuple(snapshots))
                                send_result_to_daemon(
                                    result=DaemonResult(
                                        stack=stack,
                                    ),
                                )
                    else:
                        # Disable downstream tracers
                        TRACING.set(False)

                        # No overhead is introduced!
                        result = await function(*args, **kwargs)

                    return result

                return await wrapper(*args, **kwargs)

        elif callable(function):

            @functools.wraps(function)
            def isolated_wrapper(*args: Any, **kwargs: Any) -> Any:

                @functools.wraps(function)
                def wrapper(*args: Any, **kwargs: Any) -> Any:
                    if LEVEL.get() == 0:
                        LOGGER.set(log_to)

                    if enabled and TRACING.get():
                        with increase_counter(LEVEL):
                            record_event('call', function, function_name)
                            result = function(*args, **kwargs)
                            record_event('return', function, function_name)

                            if LEVEL.get() == 1:
                                stack = STACK.get()
                                analyze_stack(stack)
                                send_result_to_daemon(
                                    result=DaemonResult(
                                        stack=stack,
                                    ),
                                )
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


_DEFAULT_TRACER: Callable[[Callable[..., Any]], Callable[..., Any]] = trace()


def call(function: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
    return _DEFAULT_TRACER(function)(*args, **kwargs)
