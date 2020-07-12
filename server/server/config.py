# Standard library
import os
import json
from typing import (
    Tuple,
)

# Third party libraries
from jwcrypto import (
    jwk,
)

HTTP_AUTH_HEADER: str = 'authorization'
HTTP_AUTH_COOKIE: str = 'session'

JWT_ENCRYPTION_KEY: jwk.JWK = \
    jwk.JWK(**json.loads(os.environ['JWT_ENCRYPTION_KEY']))
JWT_SIGNING_KEY: jwk.JWK = \
    jwk.JWK(**json.loads(os.environ['JWT_SIGNING_KEY']))
MEASURE_INTERVALS: Tuple[int, ...] = (
    1,  # 1 second
    5,  # 5 second
    15,  # 15 second
    60,  # 1 minute
    300,  # 5 minutes
    900,  # 15 minutes
    3600,  # 1 hour
    7200,  # 2 hour
    21600,  # 6 hour
    86400,  # 1 day
    604800,  # 1 week
    2592000,  # 1 month
)
TTL_PER_SECOND: int = 60
