# Standard library
import json
from typing import (
    Any,
    Dict,
)

# Third party libraries
from jwcrypto.jwe import (
    JWE,
)
from jwcrypto.jwt import (
    JWT,
)

# Local libraries
from backend.config import (
    JWT_ENCRYPTION_KEY,
    JWT_SIGNING_KEY,
)


def serialize(claims: dict) -> str:
    jwt: JWT = JWT(
      claims=JWE(
        algs=[
            'A256GCM',
            'A256GCMKW',
        ],
        plaintext=json.dumps(claims).encode('utf-8'),
        protected={
          'alg': 'A256GCMKW',
          'enc': 'A256GCM',
        },
        recipient=JWT_ENCRYPTION_KEY,
      ).serialize(),
      header={
        'alg': 'HS512',
      },
    )
    jwt.make_signed_token(JWT_SIGNING_KEY)

    return jwt.serialize()


def deserialize(jwt: str) -> Dict[str, Any]:
    jwt: JWT = JWT(
        key=JWT_SIGNING_KEY,
        jwt=jwt,
    )
    jwe = JWE()
    jwe.deserialize(jwt.claims)
    jwe.decrypt(JWT_ENCRYPTION_KEY)

    return json.loads(jwe.payload.decode('utf-8'))
