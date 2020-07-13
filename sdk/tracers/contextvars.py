# Standard library
from contextvars import (
    ContextVar,
)
from typing import (
    List,
)

# Local libraries
from tracers.containers import (
    Frame,
)

LEVEL: ContextVar[int] = \
    ContextVar('LEVEL', default=0)
STACK: ContextVar[List[Frame]] = \
    ContextVar('STACK', default=[])
TRACING: ContextVar[bool] = \
    ContextVar('TRACING', default=True)
