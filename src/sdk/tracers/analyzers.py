# Standard library
from itertools import groupby
from operator import (
    attrgetter,
    itemgetter,
)
from typing import (
    NamedTuple,
    Tuple,
)

# Local libraries
from tracers.containers import (
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

Result = NamedTuple('Result', [
    ('counter', int),
    ('function', str),
    ('indentation', str),
    ('level', int),
    ('net_time_ratio', float),
    ('net_time_seconds', float),
    ('raw_time_ratio', float),
    ('raw_time_seconds', float),
    ('relative_timestamp', float),
])


def analyze_loop_snapshots(
    snapshots: Tuple[LoopSnapshot, ...],
) -> None:
    top_snapshots: Tuple[LoopSnapshot, ...] = tuple(sorted(
        [
            snapshot
            for snapshot in snapshots
            if snapshot.block_duration_ratio > 1.0 + LOOP_SKEW_TOLERANCE
        ],
        key=attrgetter('real_tick_duration'),
        reverse=True,
    ))

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


def analyze_stack(  # pylint: disable=too-many-locals
    stack: Tuple[Frame, ...],
) -> None:
    stack_levels: Tuple[int, ...] = \
        tuple(map(attrgetter('level'), stack))

    total_time_seconds: float = \
        delta(stack[0].timestamp, stack[-1].timestamp)

    log()
    log(f'{CHAR_INFO} Finished transaction: {total_time_seconds:.2f} seconds')
    log()
    log('     # Timestamp                Net              Total    Call Chain')
    log()

    counter: int = 0
    results: Tuple[Result, ...] = ()
    accumulator: Tuple[Result, ...] = ()
    for index, frame in enumerate(stack):
        if frame.event == 'call':
            counter += 1

            frame_childs: Tuple[Frame, ...] = \
                stack[index:stack_levels.index(frame.level, index + 1) + 1]

            raw_time_seconds: float = \
                delta(frame_childs[0].timestamp, frame_childs[-1].timestamp)

            net_time_seconds: float = \
                raw_time_seconds - sum([
                    +x.timestamp if x.event == 'return' else -x.timestamp
                    for x in frame_childs
                    if x.level == frame.level + 1
                ])

            results += (Result(
                counter=counter,
                function=frame.function,
                indentation=(
                    (3 * CHAR_SPACE + CHAR_BROKEN_BAR) * (frame.level - 1) +
                    (3 * CHAR_SPACE + CHAR_CHECK_MARK)
                ),
                level=frame.level,
                net_time_ratio=100.0 * divide(
                    numerator=net_time_seconds,
                    denominator=total_time_seconds,
                    on_zero_denominator=1.0,
                ),
                net_time_seconds=net_time_seconds,
                relative_timestamp=delta(stack[0].timestamp, frame.timestamp),
                raw_time_ratio=100.0 * divide(
                    numerator=raw_time_seconds,
                    denominator=total_time_seconds,
                    on_zero_denominator=1.0,
                ),
                raw_time_seconds=raw_time_seconds,
            ),)

    if results:
        accumulator += (results[0],)
        accumulator = flush_accumulator(accumulator)

    for index, result in enumerate(results[1:-1], start=1):
        accumulator += (result,)

        if ((result.level != results[index - 1].level or
                result.function != results[index - 1].function) and
            (result.level != results[index + 1].level or
                result.function != results[index + 1].function)):
            accumulator = flush_accumulator(accumulator)

    if len(results) > 1:
        accumulator += (results[-1],)
        accumulator = flush_accumulator(accumulator)

    log()
    log('           Count                Net              Total    Function')
    log()

    key = attrgetter('function')

    for (
        function,
        net_time_ratio,
        net_time_seconds,
        raw_time_ratio,
        raw_time_seconds,
        times_called
    ) in sorted(
        (
            (
                function,
                sum(map(attrgetter('net_time_ratio'), group)),
                sum(map(attrgetter('net_time_seconds'), group)),
                sum(map(attrgetter('raw_time_ratio'), group)),
                sum(map(attrgetter('raw_time_seconds'), group)),
                len(group),
            )
            for function, group_iter in groupby(
                sorted(
                    results,
                    key=key,
                ),
                key=key,
            )
            for group in [tuple(group_iter)]
        ),
        key=itemgetter(2),
        reverse=True,
    ):
        log(
            f'{times_called:>16}',
            f'{net_time_seconds:>8.2f}s',
            f'[{net_time_ratio:>5.1f}%]',
            f'{raw_time_seconds:>8.2f}s',
            f'[{raw_time_ratio:>5.1f}%]',
            f'{3 * CHAR_SPACE + CHAR_CHECK_MARK}',
            f'{function}',
        )


def flush_accumulator(accumulator: Tuple[Result, ...]) -> Tuple[Result, ...]:
    if accumulator:
        times: str = f'{len(accumulator)} times: ' * (len(accumulator) > 1)

        log(
            f'{accumulator[0].counter:>6}',
            f'{accumulator[0].relative_timestamp:>8.2f}s',
            f'{sum(map(attrgetter("net_time_seconds"), accumulator)):>8.2f}s',
            f'[{sum(map(attrgetter("net_time_ratio"), accumulator)):>5.1f}%]',
            f'{sum(map(attrgetter("raw_time_seconds"), accumulator)):>8.2f}s',
            f'[{sum(map(attrgetter("raw_time_ratio"), accumulator)):>5.1f}%]',
            f'{accumulator[0].indentation}',
            f'{times}{accumulator[0].function}',
        )

    return ()
