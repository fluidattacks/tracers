# Standard library
import functools
from typing import (
    Any,
    cast,
    NamedTuple,
    Optional,
    Tuple,
)
import secrets

# Third party libraries
import graphql.execution.base
import starlette.datastructures
import starlette.requests
import starlette.responses
import starlette.types
import tracers.function

# Local libraries
import server.config
import server.domain.tenant
import server.utils.function
import server.utils.jwt
from server.typing import (
    T,
)


class VerifiedClaims(NamedTuple):
    tenant_id: str


class AuthenticationMidleware:

    def __init__(
        self,
        app: starlette.types.ASGIApp,
        authentication_path: str,
        authentication_required_paths: Tuple[str, ...],
    ):
        self.app: starlette.types.ASGIApp = app
        self.authentication_path: str = authentication_path
        self.authentication_required_paths: Tuple[str, ...] = \
            authentication_required_paths

    @tracers.function.trace()
    async def __call__(
        self,
        scope: starlette.types.Scope,
        receive: starlette.types.Receive,
        send: starlette.types.Send,
    ) -> None:
        path: str = scope.get('root_path', '') + scope['path']
        verified_claims: Optional[VerifiedClaims] = None

        # If this path is below any authentication required path protect it
        if any(map(path.startswith, self.authentication_required_paths)):
            request = starlette.requests.Request(scope)

            request_claims: str
            if server.config.HTTP_AUTH_HEADER in request.headers:
                request_claims = \
                    request.headers[server.config.HTTP_AUTH_HEADER]
            elif server.config.HTTP_AUTH_COOKIE in request.cookies:
                request_claims = \
                    request.cookies[server.config.HTTP_AUTH_COOKIE]
            else:
                raise PermissionError('Expected cookie or header authc')

            kind, token = request_claims.split(' ', maxsplit=1)

            if kind not in ['Bearer']:
                raise TypeError('Expected a Bearer Token')

            verified_claims = VerifiedClaims(**{
                claim_name: claim_value
                for claims in [await server.utils.jwt.deserialize(token)]
                for claim_name, claim_value in claims.items()
                if claim_name in VerifiedClaims._fields
            })

        scope.setdefault('state', {})
        scope['state']['verified_claims'] = verified_claims

        await self.app(scope, receive, send)


async def handle_session_start_request(
    request: starlette.requests.Request,
) -> starlette.responses.Response:
    params = await request.form()

    tenant_id: str = params['tenant_id']
    tenant_secret: str = params['tenant_secret']

    matches = await server.domain.tenant.get_tenant_credential(
        tenant_id=tenant_id,
    )
    tenant = matches[0]

    response = starlette.responses.Response()

    if secrets.compare_digest(
        tenant.tenant_secret_hash,
        server.utils.crypto.get_hash(
            string=tenant_secret,
            salt=tenant.tenant_secret_salt,
        )
    ):
        session_token = server.utils.jwt.serialize(
            claims={
                'tenant_id': tenant.tenant_id,
            },
            ttl=server.config.SESSION_DURATION_SECONDS,
        )

        response.status_code = 200
        response.set_cookie(
            key=server.config.HTTP_AUTH_COOKIE,
            value=f'Bearer {session_token}',
            max_age=server.config.SESSION_DURATION_SECONDS,
            secure=False,
            httponly=True,
            samesite='lax',
        )
    else:
        response.status_code = 403

    return response
