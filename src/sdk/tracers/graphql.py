# Standard library
import aiohttp
import json
from os import environ
from typing import (
    Optional,
)

# Third party libraries
import aiogqlc

# Local libraries
from tracers.config import (
    Config,
)


class GraphQLClient(aiogqlc.GraphQLClient):

    async def execute(
            self,
            query: str,
            variables: dict = None,
            operation: str = None,
        ) -> aiohttp.ClientResponse:
        connector = aiohttp.TCPConnector(verify_ssl=False)
        timeout = aiohttp.ClientTimeout(
            total=None,
            connect=None,
            sock_connect=None,
            sock_read=None,
        )

        async with aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            trust_env=True,
        ) as session:
            headers = self.prepare_headers()
            headers[aiohttp.hdrs.CONTENT_TYPE] = 'application/json'
            data = json.dumps(
                self.prepare_json_data(query, variables, operation),
            )

            async with session.post(
                self.endpoint,
                data=data,
                headers=headers,
            ) as response:
                return await response.read()


if all([
    Config.api_token,
    Config.endpoint_url,
]):
    CLIENT: Optional[GraphQLClient] = GraphQLClient(
        endpoint=Config.endpoint_url,
        headers={
            'Authorization': f'Bearer {Config.api_token}'
        },
    )
else:
    CLIENT = None
