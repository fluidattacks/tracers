# Standard library
from contextvars import (
    ContextVar,
)
from typing import (
    Optional,
    Tuple,
    TextIO,
)

# Local libraries
from tracers.containers import (
    Frame,
)

LEVEL: ContextVar[int] = \
    ContextVar('LEVEL', default=0)
LOGGING_TO: ContextVar[Optional[TextIO]] = \
    ContextVar('LOGGING_TO', default=None)
STACK: ContextVar[Tuple[Frame, ...]] = \
    ContextVar('STACK', default=())
TRACING: ContextVar[bool] = \
    ContextVar('TRACING', default=True)
