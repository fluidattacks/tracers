# Standard library
import asyncio
import contextlib
import contextvars
import functools
import threading
from typing import (
    Any,
    Callable,
    cast,
    List,
    Optional,
)

# Local libraries
from tracers.constants import (
    LOOP_CHECK_INTERVAL,
    T,
)
from tracers.containers import (
    DaemonResult,
    Frame,
    LoopSnapshot,
)
from tracers.contextvars import (
    LEVEL,
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
) -> None:
    STACK.get().append(Frame(
        event=event,
        function=get_function_id(function),
        level=LEVEL.get(),
        timestamp=get_monotonic_time(),
    ))


def trace(  # noqa: MC0001
    *,
    enabled: bool = True,
    overridden_function: Optional[Callable[..., Any]] = None,
) -> Callable[[T], T]:

    def decorator(function: Callable[..., Any]) -> Callable[..., Any]:

        display_function = overridden_function or function

        if asyncio.iscoroutinefunction(function):

            @functools.wraps(function)
            async def isolated_wrapper(*args: Any, **kwargs: Any) -> Any:

                @functools.wraps(function)
                async def wrapper(*args: Any, **kwargs: Any) -> Any:
                    if enabled and TRACING.get():
                        with condition() as should_measure_loop_skew, \
                                increase_counter(LEVEL):
                            if LEVEL.get() == 1:
                                STACK.set([])
                                should_measure_loop_skew.set()
                                loop_snapshots: List[LoopSnapshot] = []
                                measure_loop_skew(
                                    should_measure_loop_skew,
                                    loop_snapshots,
                                )

                            record_event('call', display_function)
                            result = await function(*args, **kwargs)
                            record_event('return', display_function)

                            if LEVEL.get() == 1:
                                send_result_to_daemon(
                                    result=DaemonResult(
                                        loop_snapshots=loop_snapshots,
                                        stack=STACK.get(),
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
                    if enabled and TRACING.get():
                        with increase_counter(LEVEL):
                            if LEVEL.get() == 1:
                                STACK.set([])

                            record_event('call', display_function)
                            result = function(*args, **kwargs)
                            record_event('return', display_function)

                            if LEVEL.get() == 1:
                                send_result_to_daemon(
                                    result=DaemonResult(
                                        loop_snapshots=[],
                                        stack=STACK.get(),
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
                f'Expected callable or coroutine function, '
                f'got: {type(function)}'
            )

        return isolated_wrapper

    return cast(Callable[[T], T], decorator)


_DEFAULT_TRACER: Callable[[T], T] = trace()


def call(function: Callable[..., T], *args: Any, **kwargs: Any) -> T:
    return _DEFAULT_TRACER(function)(*args, **kwargs)
