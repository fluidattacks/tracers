# Standard library
import os
from typing import (
    NamedTuple,
)

# Local libraries
from tracers.constants import (
    LOGGER_DAEMON,
)


def _get(var_name: str, var_default: str) -> str:
    var_value: str = os.environ.get(var_name, var_default)

    if var_name in [
        'TRACERS_API_TOKEN',
    ]:
        LOGGER_DAEMON.info('%s = %s', var_name, "<set>" if var_value else "")
    else:
        LOGGER_DAEMON.info('%s = %s', var_name, var_value)

    return var_value


# Runtime constants
class Config(NamedTuple):
    api_token: str
    daemon_interval: float
    daemon_logging: bool
    endpoint_url: str
    system_id: str

    api_token_source: str = 'TRACERS_API_TOKEN'
    daemon_interval_source: str = 'TRACERS_DAEMON_SECONDS_BETWEEN_UPLOADS'
    daemon_logging_source: str = 'TRACERS_DAEMON_LOGGING'
    endpoint_url_source: str = 'TRACERS_ENDPOINT_URL'
    system_id_source: str = 'TRACERS_SYSTEM_ID'


CONFIG = Config(
    api_token=_get('TRACERS_API_TOKEN', ''),
    daemon_interval=float(_get('TRACERS_DAEMON_SECONDS_BETWEEN_UPLOADS', '1')),
    daemon_logging=_get('TRACERS_DAEMON_LOGGING', 'true').lower() == 'true',
    endpoint_url=_get('TRACERS_ENDPOINT_URL', ''),
    system_id=_get('TRACERS_SYSTEM_ID', 'default'),
)
