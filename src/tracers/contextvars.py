# Standard library
from contextvars import (
    ContextVar,
)
from typing import (
    Any,
    Callable,
    List,
    Tuple,
)

# Local libraries
from tracers.containers import (
    Frame,
    LoopSnapshot,
)

LEVEL: ContextVar[int] = \
    ContextVar('LEVEL')
LOOP_SNAPSHOTS: ContextVar[List[LoopSnapshot]] = \
    ContextVar('LOOP_SNAPSHOTS')
STACK: ContextVar[List[Frame]] = \
    ContextVar('STACK')
TRACING: ContextVar[bool] = \
    ContextVar('TRACING')

ALL: Tuple[Tuple[ContextVar, Callable[[], Any]], ...] = (
    (LEVEL, lambda: 0),
    (LOOP_SNAPSHOTS, lambda: []),
    (STACK, lambda: []),
    (TRACING, lambda: True),
)
