# Standard library
from datetime import datetime
import json
from typing import (
    Any,
    Dict,
    Optional,
)

# Third party libraries
from jwcrypto.jwe import (
    JWE,
)
from jwcrypto.jwt import (
    JWT,
)
import tracers.function

# Local libraries
import server.config
import server.utils.aio


@tracers.function.trace()
def serialize(claims: dict, ttl: Optional[float] = None) -> str:
    now: float = datetime.now().timestamp()

    default_claims: dict = {
        'iat': now,
        'nbf': now,
    }

    if ttl:
        default_claims['exp'] = now + ttl

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
            recipient=server.config.JWT_ENCRYPTION_KEY,
        ).serialize(),
        default_claims=default_claims,
        header={
            'alg': 'HS512',
        },
    )
    jwt.make_signed_token(server.config.JWT_SIGNING_KEY)

    return jwt.serialize()


@tracers.function.trace()
def deserialize(jwt: str) -> Dict[str, Any]:
    jwt: JWT = JWT(
        key=server.config.JWT_SIGNING_KEY,
        jwt=jwt,
    )
    jwe = JWE()
    jwe.deserialize(jwt.claims)
    jwe.decrypt(server.config.JWT_ENCRYPTION_KEY)

    return json.loads(jwe.payload.decode('utf-8'))
