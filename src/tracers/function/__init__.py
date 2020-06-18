# Standard library
import asyncio
import contextlib
import functools
import inspect
import operator
import time
import uuid
from contextvars import (
    ContextVar,
    Token,
)
from typing import (
    Any,
    Callable,
    List,
    NamedTuple,
    Tuple,
)

# Local libraries
from tracers.constants import (
    CHAR_BROKEN_BAR,
    CHAR_CHECK_MARK,
    CHAR_INFO,
    CHAR_SPACE,
    CHAR_SUPERSCRIPT_ONE,
    LOOP_CHECK_INTERVAL,
    LOOP_SKEW_TOLERANCE,
)

# Containers
Frame = NamedTuple('Frame', [
    ('event', str),
    ('function', str),
    ('level', int),
    ('timestamp', float),
])
LoopSnapshot = NamedTuple('LoopSnapshot', [
    ('block_duration_ratio', float),
    ('wanted_tick_duration', float),
    ('real_tick_duration', float),
    ('timestamp', float),
])

# Contextvars
TRACING: ContextVar[bool] = ContextVar('TRACING', default=True)
LEVEL: ContextVar[int] = ContextVar('LEVEL', default=0)
STACK: ContextVar[List[Frame]] = ContextVar('STACK', default=[])

LOOP_SNAPSHOTS: ContextVar[List[LoopSnapshot]] = \
    ContextVar('LOOP_SNAPSHOTS', default=[])

ALL_CONTEXTVARS: Tuple[Tuple[ContextVar, Callable[[], Any]], ...] = (
    (TRACING, lambda: True),
    (LEVEL, lambda: 0),
    (STACK, lambda: []),
    (LOOP_SNAPSHOTS, lambda: []),
)


def divide(
    *,
    numerator: float,
    denominator: float,
    on_zero_denominator: float,
) -> float:
    return \
        on_zero_denominator if denominator == 0.0 else numerator / denominator


def get_function_id(function: Callable, function_name: str = '') -> str:
    # Adding decorators to a function modify its metadata
    #   Fortunately functools' wrapped functions keep a reference to the parent
    while hasattr(function, '__wrapped__'):
        function = getattr(function, '__wrapped__')

    signature: str = '(...)'
    with contextlib.suppress(ValueError):
        signature = str(inspect.signature(function))

    module: str = function.__module__
    name: str = function_name or function.__name__
    prefix = 'async ' * asyncio.iscoroutinefunction(function)
    signature = signature if len(signature) < 48 else '(...)'

    if module not in {'__main__'}:
        return f'{prefix}{module}.{name}{signature}'

    return f'{prefix}{name}{signature}'


def reset_contextvars():

    def reset_context_var(
        contextvar: ContextVar,
        default_value_creator: Callable[[], Any],
    ) -> None:
        obj = contextvar.get(None)

        if obj:
            if isinstance(obj, list):
                # Delete all elements
                obj.clear()
            elif isinstance(obj, (bool, int)):
                # This never leaks
                pass
            else:
                raise TypeError(f'Missing handler for type: {type(obj)}')

        # Delete reference
        del obj

        # Re-initialize to its default value
        var.set(default_value_creator())

    for var, default_value_creator in ALL_CONTEXTVARS:
        reset_context_var(var, default_value_creator)


@contextlib.contextmanager
def increase_counter(contextvar):
    token: Token = contextvar.set(contextvar.get() + 1)
    try:
        yield
    finally:
        contextvar.reset(token)


def measure_loop_skew(clock_id: int):

    def callback_handler(
        wanted_tick_duration: float,
        start_timestamp: float,
    ):
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

    def schedule_callback(wanted_tick_duration: float):
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
    function: Callable,
    function_name: str = '',
):
    STACK.get().append(Frame(
        event=event,
        function=get_function_id(function, function_name),
        level=LEVEL.get(),
        timestamp=time.clock_gettime(clock_id),
    ))


def analyze_stack(stack: List[Frame]):
    stack_levels: List[int] = [frame.level for frame in stack]

    total_time_seconds: float = \
        stack[-1].timestamp - stack[0].timestamp

    print()
    print(
        f'{CHAR_INFO} Finished transaction: {uuid.uuid4().hex}, '
        f'{total_time_seconds:.2f} seconds')
    print()
    print('  #    Timestamp       %     Total    Nested Call Chain')
    print()

    counter: int = 0
    for index, frame in enumerate(stack):
        indentation: str = (
            (CHAR_SPACE * 3 + CHAR_BROKEN_BAR) * (frame.level - 1)
            + (CHAR_SPACE * 3 + CHAR_CHECK_MARK)
        )

        if frame.event == 'call':
            counter += 1
            frame_childs: List[Frame] = \
                stack[index:stack_levels.index(frame.level, index + 1) + 1]

            relative_timestamp: float = \
                frame.timestamp - stack[0].timestamp

            raw_time_seconds: float = \
                frame_childs[-1].timestamp - frame_childs[0].timestamp

            raw_time_ratio: float = 100.0 * divide(
                numerator=raw_time_seconds,
                denominator=total_time_seconds,
                on_zero_denominator=1.0,
            )

            print(
                f'{counter:>6} '
                f'{relative_timestamp:>8.2f}s '
                f'{raw_time_ratio:>6.1f}% '
                f'{raw_time_seconds:>8.2f}s '
                f'{indentation} '
                f'{frame.function}'
            )


def analyze_loop_snapshots(
    snapshots: List[LoopSnapshot],
):
    top_snapshots: List[LoopSnapshot] = sorted(
        [
            snapshot
            for snapshot in snapshots
            if snapshot.block_duration_ratio > 1.0 + LOOP_SKEW_TOLERANCE
        ],
        key=operator.attrgetter('real_tick_duration'),
        reverse=True,
    )

    if top_snapshots:
        print()
        print(
            f'  Some blocks (skews) occurred in the event loop'
            f' {CHAR_SUPERSCRIPT_ONE}'
        )
        print()
        print('  #    Timestamp     Delay')
        print()
        initial_timestamp: float = snapshots[0].timestamp
        for counter, snapshot in enumerate(top_snapshots):
            skew: float = \
                snapshot.real_tick_duration - snapshot.wanted_tick_duration

            print(
                f'{counter:>6} '
                f'{snapshot.timestamp - initial_timestamp:>8.2f}s '
                f'{skew:>8.2f}s '
            )
        print()
        print(
            f'  {CHAR_SUPERSCRIPT_ONE}'
            f' Consider reviewing them carefully'
            f' to improve the overall system throughput'
        )


def _get_wrapper(  # noqa: MC001
    *,
    clock_id: int = time.CLOCK_MONOTONIC,
    do_trace: bool = True,
    function_name: str = '',
    loop_snapshots_analyzer: Callable[[List[LoopSnapshot]], None] =
    analyze_loop_snapshots,
    stack_analyzer: Callable[[List[Frame]], None] =
    analyze_stack,
) -> Callable:

    def decorator(function: Callable) -> Callable:

        if not do_trace or not TRACING.get():

            # No overhead is introduced
            wrapper = function

            # Any downstream tracer is also disabled
            TRACING.set(False)

        elif asyncio.iscoroutinefunction(function):

            @functools.wraps(function)
            async def wrapper(*args, **kwargs):
                if LEVEL.get() == 0:
                    reset_contextvars()

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
            def wrapper(*args, **kwargs):
                if LEVEL.get() == 0:
                    reset_contextvars()

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
):
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
):
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
):
    return _get_wrapper(
        clock_id=time.CLOCK_MONOTONIC,
        do_trace=do_trace,
        function_name=function_name,
        loop_snapshots_analyzer=loop_snapshots_analyzer,
        stack_analyzer=stack_analyzer,
    )


def trace(
    function: Callable = None,
    *,
    do_trace: bool = True,
    function_name: str = '',
    loop_snapshots_analyzer: Callable[[List[LoopSnapshot]], None] =
    analyze_loop_snapshots,
    stack_analyzer: Callable[[List[Frame]], None] =
    analyze_stack,
):
    wrapper = trace_monotonic(
        do_trace=do_trace,
        function_name=function_name,
        loop_snapshots_analyzer=loop_snapshots_analyzer,
        stack_analyzer=stack_analyzer,
    )

    if function:
        return wrapper(function)

    return wrapper
