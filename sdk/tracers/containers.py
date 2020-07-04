# Standard library
from typing import (
    NamedTuple,
    Tuple,
)

Frame = NamedTuple('Frame', [
    ('event', str),
    ('function', str),
    ('level', int),
    ('timestamp', float),
])

DaemonResult = NamedTuple('DaemonResult', [
    ('stack', Tuple[Frame, ...]),
])

LoopSnapshot = NamedTuple('LoopSnapshot', [
    ('block_duration_ratio', float),
    ('real_tick_duration', float),
    ('timestamp', float),
    ('wanted_tick_duration', float),
])
