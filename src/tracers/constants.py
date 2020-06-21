# Standard library
from typing import (
    TypeVar,
)

CHAR_SPACE = chr(0x20)
CHAR_INFO = chr(0x1F6C8) + CHAR_SPACE
CHAR_CHECK_MARK = chr(0X2713)
CHAR_BROKEN_BAR = chr(0xA6)
CHAR_SUPERSCRIPT_ONE = chr(0x00B9)

LOOP_CHECK_INTERVAL: float = 0.01
LOOP_SKEW_TOLERANCE: float = 1.0

T = TypeVar('T')
