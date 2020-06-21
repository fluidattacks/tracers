# Standard library
import io
import contextlib
import operator
from typing import (
    List,
    NamedTuple,
)
from uuid import uuid4

# Local libraries
from tracers.containers import (
    DaemonResult,
    Frame,
    LoopSnapshot,
)
from tracers.constants import (
    CHAR_BROKEN_BAR,
    CHAR_CHECK_MARK,
    CHAR_INFO,
    CHAR_SPACE,
    CHAR_SUPERSCRIPT_ONE,
    LOOP_SKEW_TOLERANCE,
)
from tracers.utils import (
    delta,
    divide,
    log,
)
from tracers.daemon import (
    send_result_to_daemon,
)

Result = NamedTuple('Result', [
    ('counter', int),
    ('relative_timestamp', float),
    ('raw_time_ratio', float),
    ('raw_time_seconds', float),
    ('indentation', str),
    ('level', int),
    ('function', str),
])


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
        log()
        log('  Some blocks (skews) occurred in the event loop',
            CHAR_SUPERSCRIPT_ONE)
        log()
        log('  #    Timestamp     Delay')
        log()
        initial_timestamp: float = snapshots[0].timestamp
        for counter, snapshot in enumerate(top_snapshots):
            skew: float = delta(
                snapshot.wanted_tick_duration,
                snapshot.real_tick_duration,
            )

            log(f'{counter:>6}',
                f'{delta(initial_timestamp, snapshot.timestamp):>8.2f}s',
                f'{skew:>8.2f}s')
        log()
        log(f'  {CHAR_SUPERSCRIPT_ONE}',
            'Consider reviewing them carefully',
            'to improve the overall system throughput')


def analyze_stack(stack: List[Frame]):
    with io.StringIO() as buffer:
        with contextlib.redirect_stdout(buffer):
            _analyze_stack(stack)

        buffer.seek(0)
        stdout = buffer.read()

    log(stdout)
    send_result_to_daemon(DaemonResult(
        stack=stack,
        stdout=stdout,
    ))


def _analyze_stack(stack: List[Frame]):
    stack_levels: List[int] = \
        list(map(operator.attrgetter('level'), stack))

    total_time_seconds: float = \
        delta(stack[0].timestamp, stack[-1].timestamp)

    log()
    log(f'{CHAR_INFO} Finished transaction: {uuid4().hex},',
        f'{total_time_seconds:.2f} seconds')
    log()
    log('  #    Timestamp       %     Total    Nested Call Chain')
    log()

    counter: int = 0
    results: List[Result] = []
    accumulator: List[Result] = []
    for index, frame in enumerate(stack):
        if frame.event == 'call':
            counter += 1

            frame_childs: List[Frame] = \
                stack[index:stack_levels.index(frame.level, index + 1) + 1]

            raw_time_seconds: float = \
                delta(frame_childs[0].timestamp, frame_childs[-1].timestamp)

            results.append(Result(
                counter=counter,
                relative_timestamp=delta(stack[0].timestamp, frame.timestamp),
                raw_time_ratio=100.0 * divide(
                    numerator=raw_time_seconds,
                    denominator=total_time_seconds,
                    on_zero_denominator=1.0,
                ),
                raw_time_seconds=raw_time_seconds,
                level=frame.level,
                indentation=(
                    (CHAR_SPACE * 3 + CHAR_BROKEN_BAR) * (frame.level - 1) +
                    (CHAR_SPACE * 3 + CHAR_CHECK_MARK)
                ),
                function=frame.function,
            ))

    if results:
        accumulator.append(results[0])
        flush_accumulator(accumulator)

    for index, result in enumerate(results[1:-1], start=1):
        accumulator.append(result)

        if ((result.level != results[index - 1].level or
                result.function != results[index - 1].function) and
            (result.level != results[index + 1].level or
                result.function != results[index + 1].function)):
            flush_accumulator(accumulator)

    if len(results) > 1:
        accumulator.append(results[-1])
        flush_accumulator(accumulator)


def flush_accumulator(accumulator: List[Result]):
    if accumulator:
        times: str = f'{len(accumulator)} times: ' * (len(accumulator) > 1)

        log(
            f'{accumulator[0].counter:>6}',
            f'{accumulator[0].relative_timestamp:>8.2f}s',
            f'{sum(r.raw_time_ratio for r in accumulator):>6.1f}%',
            f'{sum(r.raw_time_seconds for r in accumulator):>8.2f}s',
            f'{accumulator[0].indentation}',
            f'{times}{accumulator[0].function}',
        )
        accumulator.clear()
