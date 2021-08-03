# Standard library
from typing import (
    Optional,
)

# Third party libraries
from aiogqlc import GraphQLClient

# Local libraries
from tracers.config import (
    CONFIG,
)

REQUIRED_VARIABLES = [
    (CONFIG.api_token, CONFIG.api_token_source),
    (CONFIG.endpoint_url, CONFIG.endpoint_url_source),
    (CONFIG.system_id, CONFIG.system_id_source),
]

if all(var for var, _ in REQUIRED_VARIABLES):
    CLIENT: Optional[GraphQLClient] = GraphQLClient(
        endpoint=CONFIG.endpoint_url,
        headers={
            'authorization': f'Bearer {CONFIG.api_token}'
        },
    )
else:
    CLIENT = None
