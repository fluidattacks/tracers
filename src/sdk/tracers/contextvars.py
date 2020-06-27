# Standard library
from contextvars import (
    ContextVar,
)
from typing import (
    Any,
    Tuple,
)

# Local libraries
from tracers.containers import (
    Frame,
    LoopSnapshot,
)

LEVEL: ContextVar[int] = \
    ContextVar('LEVEL', default=0)
LOOP_SNAPSHOTS: ContextVar[Tuple[LoopSnapshot, ...]] = \
    ContextVar('LOOP_SNAPSHOTS')
STACK: ContextVar[Tuple[Frame, ...]] = \
    ContextVar('STACK')
TRACING: ContextVar[bool] = \
    ContextVar('TRACING', default=True)

RESETABLE: Tuple[Tuple[ContextVar[Any], Any], ...] = (
    (LEVEL, 0),
    (LOOP_SNAPSHOTS, ()),
    (STACK, ()),
)


def reset_all() -> None:
    for var, default_value in RESETABLE:
        reset_one(var, default_value)


def reset_one(
    contextvar: ContextVar[Any],
    default_value: Any,
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
    contextvar.set(default_value)
