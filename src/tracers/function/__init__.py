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
    Callable,
    List,
    NamedTuple,
    Tuple,
)

# Constants
CHAR_SPACE = chr(0x20)
CHAR_INFO = chr(0x1F6C8) + CHAR_SPACE
CHAR_CHECK_MARK = chr(0X2713)
CHAR_BROKEN_BAR = chr(0xA6)
CHAR_SUPERSCRIPT_ONE = chr(0x00B9)

# Containers
Frame = NamedTuple('Frame', [
    ('event', str),
    ('function', str),
    ('level', int),
    ('timestamp', float),
])
EventLoopTimerSnapshot = NamedTuple('EventLoopTimerSnapshot', [
    ('block_duration_ratio', float),
    ('expected_tick_duration', float),
    ('real_tick_duration', float),
    ('timestamp', float),
    ('was_blocked', bool),
])

# Contextvars
DO_TRACE: ContextVar[bool] = ContextVar('DO_TRACE', default=True)
LEVEL: ContextVar[int] = ContextVar('LEVEL', default=0)
STACK: ContextVar[List[Frame]] = ContextVar('STACK', default=[])

EVENT_LOOP_TIMER_SNAPSHOTS: ContextVar[List[EventLoopTimerSnapshot]] = \
    ContextVar('EVENT_LOOP_TIMER_SNAPSHOTS', default=[])


def divide(
    *,
    numerator: float,
    denominator: float,
    on_zero_denominator: float,
) -> float:
    return \
        numerator / denominator if denominator > 0.0 else on_zero_denominator


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


@contextlib.contextmanager
def increase_counter(contextvar):
    token: Token = contextvar.set(contextvar.get() + 1)
    try:
        yield
    finally:
        contextvar.reset(token)


def measure_event_loop_skew(clock_id: int):

    def callback_handler(
        expected_tick_duration: float,
        start_timestamp: float,
    ):
        tolerance: float = 1.05
        timestamp: float = time.clock_gettime(clock_id)
        real_tick_duration: float = timestamp - start_timestamp
        block_duration_ratio: float = divide(
            numerator=real_tick_duration,
            denominator=expected_tick_duration,
            on_zero_denominator=1.0,
        )

        EVENT_LOOP_TIMER_SNAPSHOTS.get().append(EventLoopTimerSnapshot(
            block_duration_ratio=block_duration_ratio,
            expected_tick_duration=expected_tick_duration,
            real_tick_duration=real_tick_duration,
            timestamp=start_timestamp,
            was_blocked=block_duration_ratio >= tolerance,
        ))

        if LEVEL.get() == 1:
            schedule_callback(expected_tick_duration)

    def schedule_callback(expected_tick_duration: float):
        with contextlib.suppress(RuntimeError):
            callback_handler_args: Tuple[float, float] = (
                expected_tick_duration, time.clock_gettime(clock_id),
            )

            loop = asyncio.get_running_loop()
            loop.call_later(
                expected_tick_duration,
                callback_handler,
                *callback_handler_args
            )

    if LEVEL.get() == 1:
        schedule_callback(0.1)


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

    event_loop_timer_snapshots: List[EventLoopTimerSnapshot] = \
        EVENT_LOOP_TIMER_SNAPSHOTS.get()

    top_event_loop_timer_snapshots: List[EventLoopTimerSnapshot] = sorted(
        [
            snapshot
            for snapshot in event_loop_timer_snapshots
            if snapshot.was_blocked
        ],
        key=operator.attrgetter('real_tick_duration'),
        reverse=True,
    )

    if top_event_loop_timer_snapshots:
        print()
        print(
            f'  Some blocks (skews) occurred in the event loop'
            f' {CHAR_SUPERSCRIPT_ONE}'
        )
        print()
        print('  #    Timestamp  Excess     Delay')
        print()
        initial_timestamp: float = event_loop_timer_snapshots[0].timestamp
        for counter, snapshot in enumerate(top_event_loop_timer_snapshots):
            print(
                f'{counter:>6} '
                f'{snapshot.timestamp - initial_timestamp:>8.2f}s '
                f'{100.0 * snapshot.block_duration_ratio:>6.1f}% '
                f'{snapshot.real_tick_duration:>8.2f}s '
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
    stack_analyzer: Callable[[List[Frame]], None] = analyze_stack,
) -> Callable:

    def decorator(function: Callable) -> Callable:

        if not do_trace or not DO_TRACE.get():

            # No overhead is introduced
            wrapper = function

            # Any downstream tracer is also disabled
            DO_TRACE.set(False)

        elif asyncio.iscoroutinefunction(function):

            @functools.wraps(function)
            async def wrapper(*args, **kwargs):
                if LEVEL.get() == 0:
                    EVENT_LOOP_TIMER_SNAPSHOTS.set([])
                    STACK.set([])

                with increase_counter(LEVEL):
                    measure_event_loop_skew(clock_id)
                    record_event(clock_id, 'call', function, function_name)
                    result = await function(*args, **kwargs)
                    record_event(clock_id, 'return', function, function_name)

                if LEVEL.get() == 0:
                    stack_analyzer(STACK.get())

                return result

        elif callable(function):

            @functools.wraps(function)
            def wrapper(*args, **kwargs):
                if LEVEL.get() == 0:
                    STACK.set([])

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
    stack_analyzer: Callable[[List[Frame]], None] = analyze_stack,
):
    return _get_wrapper(
        clock_id=time.CLOCK_PROCESS_CPUTIME_ID,
        do_trace=do_trace,
        function_name=function_name,
        stack_analyzer=stack_analyzer,
    )


def trace_thread(
    *,
    do_trace: bool = True,
    function_name: str = '',
    stack_analyzer: Callable[[List[Frame]], None] = analyze_stack,
):
    return _get_wrapper(
        clock_id=time.CLOCK_THREAD_CPUTIME_ID,
        do_trace=do_trace,
        function_name=function_name,
        stack_analyzer=stack_analyzer,
    )


def trace_monotonic(
    *,
    do_trace: bool = True,
    function_name: str = '',
    stack_analyzer: Callable[[List[Frame]], None] = analyze_stack,
):
    return _get_wrapper(
        clock_id=time.CLOCK_MONOTONIC,
        do_trace=do_trace,
        function_name=function_name,
        stack_analyzer=stack_analyzer,
    )


def trace(
    function: Callable = None,
    *,
    do_trace: bool = True,
    function_name: str = '',
    stack_analyzer: Callable[[List[Frame]], None] = analyze_stack,
):
    wrapper = trace_monotonic(
        do_trace=do_trace,
        function_name=function_name,
        stack_analyzer=stack_analyzer,
    )

    if function:
        return wrapper(function)

    return wrapper
