# Standard library
import os
from typing import (
    Optional,
)

# Local libraries
from tracers.utils import (
    log_stderr,
)


def _get(var_name: str) -> Optional[str]:
    var_value: str = os.environ.get(var_name)

    if var_name in [
        'TRACERS_API_TOKEN',
    ]:
        log_stderr(f'[INFO] {var_name} = {"<set>" if var_value else ""}')
    else:
        log_stderr(f'[INFO] {var_name} = {var_value}')

    return var_value


# Runtime constants
class Config:
    api_token: str = _get('TRACERS_API_TOKEN')
    endpoint_url: str = _get('TRACERS_ENDPOINT_URL')
