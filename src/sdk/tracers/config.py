# Standard library
import os
from typing import (
    NamedTuple,
    Optional,
)

# Local libraries
from tracers.constants import (
    LOGGER_DAEMON,
)


def _get(var_name: str) -> Optional[str]:
    var_value: Optional[str] = os.environ.get(var_name)

    if var_name in [
        'TRACERS_API_TOKEN',
    ]:
        LOGGER_DAEMON.info('%s = %s', var_name, "<set>" if var_value else "")
    else:
        LOGGER_DAEMON.info('%s = %s', var_name, var_value)

    return var_value


# Runtime constants
Config = NamedTuple('Config', [
    ('api_token', Optional[str]),
    ('endpoint_url', Optional[str]),
])

CONFIG = Config(
    api_token=_get('TRACERS_API_TOKEN'),
    endpoint_url=_get('TRACERS_ENDPOINT_URL'),
)
