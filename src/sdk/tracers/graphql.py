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

if all([
    CONFIG.api_token,
    CONFIG.endpoint_url,
]):
    CLIENT: Optional[GraphQLClient] = GraphQLClient(
        endpoint=CONFIG.endpoint_url,
        headers={
            'authorization': f'Bearer {CONFIG.api_token}'
        },
    )
else:
    CLIENT = None
