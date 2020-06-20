# Standard library
import operator
from typing import (
    List,
)
from uuid import uuid4

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
    divide,
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


def analyze_stack(stack: List[Frame]):
    stack_levels: List[int] = [frame.level for frame in stack]

    total_time_seconds: float = \
        stack[-1].timestamp - stack[0].timestamp

    print()
    print(
        f'{CHAR_INFO} Finished transaction: {uuid4().hex}, '
        f'{total_time_seconds:.2f} seconds')
    print()
    print('  #    Timestamp       %     Total    Nested Call Chain')
    print()

    counter: int = 0
    results: List[tuple] = []
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

            results.append((
                counter,
                relative_timestamp,
                raw_time_ratio,
                raw_time_seconds,
                indentation,
                frame.function,
            ))

    for (
        counter,
        relative_timestamp,
        raw_time_ratio,
        raw_time_seconds,
        indentation,
        function,
    ) in results:
        print(
            f'{counter:>6} '
            f'{relative_timestamp:>8.2f}s '
            f'{raw_time_ratio:>6.1f}% '
            f'{raw_time_seconds:>8.2f}s '
            f'{indentation} '
            f'{function}'
        )
