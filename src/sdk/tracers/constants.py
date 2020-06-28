# Standard library
import logging

CHAR_SPACE = chr(0x20)
CHAR_INFO = chr(0x1F6C8) + CHAR_SPACE
CHAR_CHECK_MARK = chr(0X2713)
CHAR_BROKEN_BAR = chr(0xA6)
CHAR_SUPERSCRIPT_ONE = chr(0x00B9)

LOGGER_DAEMON_HANDLER: logging.Handler = logging.StreamHandler()
LOGGER_DAEMON_HANDLER.setLevel(logging.INFO)
LOGGER_DAEMON_HANDLER.setFormatter(
    logging.Formatter('[%(levelname)s] %(message)s')
)
LOGGER_DEFAULT_HANDLER: logging.Handler = logging.StreamHandler()
LOGGER_DEFAULT_HANDLER.setLevel(logging.INFO)
LOGGER_DEFAULT_HANDLER.setFormatter(
    logging.Formatter('%(message)s')
)

LOGGER_DAEMON: logging.Logger = logging.getLogger('Tracers Daemon')
LOGGER_DAEMON.setLevel(logging.INFO)
if not LOGGER_DAEMON.hasHandlers():
    LOGGER_DAEMON.addHandler(LOGGER_DAEMON_HANDLER)

LOGGER_DEFAULT: logging.Logger = logging.getLogger('Tracers')
LOGGER_DEFAULT.setLevel(logging.INFO)
if not LOGGER_DEFAULT.hasHandlers():
    LOGGER_DEFAULT.addHandler(LOGGER_DEFAULT_HANDLER)

LOOP_CHECK_INTERVAL: float = 0.01
LOOP_SKEW_TOLERANCE: float = 1.0
