# Standard library
import os
import json

# Third party libraries
from jwcrypto import (
    jwk,
)

JWT_ENCRYPTION_KEY: jwk.JWK = \
    jwk.JWK(**json.loads(os.environ['JWT_ENCRYPTION_KEY']))
JWT_SIGNING_KEY: jwk.JWK = \
    jwk.JWK(**json.loads(os.environ['JWT_SIGNING_KEY']))
TTL_PER_SECOND: int = 60 * 60
