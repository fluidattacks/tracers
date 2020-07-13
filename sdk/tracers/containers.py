# Standard library
from typing import (
    List,
    NamedTuple,
)

Frame = NamedTuple('Frame', [
    ('event', str),
    ('function', str),
    ('level', int),
    ('timestamp', float),
])

LoopSnapshot = NamedTuple('LoopSnapshot', [
    ('block_duration_ratio', float),
    ('real_tick_duration', float),
    ('timestamp', float),
    ('wanted_tick_duration', float),
])

DaemonResult = NamedTuple('DaemonResult', [
    ('loop_snapshots', List[LoopSnapshot]),
    ('stack', List[Frame]),
])
