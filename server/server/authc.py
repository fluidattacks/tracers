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
import server.domain.user
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
                for claim_name, claim_value in (
                    server.utils.jwt.deserialize(token).items()
                )
                if claim_name in VerifiedClaims._fields
            })

        scope.setdefault('state', {})
        scope['state']['verified_claims'] = verified_claims

        await self.app(scope, receive, send)


async def handle_session_start_request(
    request: starlette.requests.Request,
) -> starlette.responses.Response:
    params = await request.form()

    user_id: str = params['user_id']
    user_secret: str = params['user_secret']

    matches = await server.domain.user.get_user_credential(user_id=user_id)
    user = matches[0]

    response = starlette.responses.Response()

    if secrets.compare_digest(
        user.user_secret_hash,
        server.utils.crypto.get_hash(
            string=user_secret,
            salt=user.user_secret_salt,
        )
    ):
        session_token = server.utils.jwt.serialize(
            claims={
                'tenant_id': user.tenant_id,
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
