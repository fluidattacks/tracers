# Standard library
from contextvars import (
    ContextVar,
)
from logging import (
    Logger,
)
from typing import (
    Optional,
    Tuple,
)

# Local libraries
from tracers.containers import (
    Frame,
)

LEVEL: ContextVar[int] = \
    ContextVar('LEVEL', default=0)
LOGGER: ContextVar[Optional[Logger]] = \
    ContextVar('LOGGER', default=None)
STACK: ContextVar[Tuple[Frame, ...]] = \
    ContextVar('STACK', default=())
TRACING: ContextVar[bool] = \
    ContextVar('TRACING', default=True)
