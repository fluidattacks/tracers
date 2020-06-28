# Standard library
import os
from typing import (
    NamedTuple,
    Optional,
)

# Local libraries
from tracers.utils import (
    log,
)


def _get(var_name: str) -> Optional[str]:
    var_value: Optional[str] = os.environ.get(var_name)

    if var_name in [
        'TRACERS_API_TOKEN',
    ]:
        log(f'[INFO] {var_name} = {"<set>" if var_value else ""}')
    else:
        log(f'[INFO] {var_name} = {var_value}')

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
