# Standard library
from typing import (
    NamedTuple,
)

Frame = NamedTuple('Frame', [
    ('event', str),
    ('function', str),
    ('level', int),
    ('signature', str),
    ('timestamp', float),
])
LoopSnapshot = NamedTuple('LoopSnapshot', [
    ('block_duration_ratio', float),
    ('wanted_tick_duration', float),
    ('real_tick_duration', float),
    ('timestamp', float),
])
