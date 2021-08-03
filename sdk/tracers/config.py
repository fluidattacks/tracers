# Standard library
import os
from typing import (
    NamedTuple,
    Optional,
)


def _get(var_name: str, var_default: Optional[str] = None) -> Optional[str]:
    var_value: Optional[str] = os.environ.get(var_name, var_default)
    return var_value


# Runtime constants
class Config(NamedTuple):
    api_token: Optional[str]
    endpoint_url: Optional[str]
    system_id: Optional[str]

    api_token_source: str = 'TRACERS_API_TOKEN'
    endpoint_url_source: str = 'TRACERS_ENDPOINT_URL'
    system_id_source: str = 'TRACERS_SYSTEM_ID'


CONFIG = Config(
    api_token=_get('TRACERS_API_TOKEN'),
    endpoint_url=_get('TRACERS_ENDPOINT_URL'),
    system_id=_get('TRACERS_SYSTEM_ID', 'default'),
)
