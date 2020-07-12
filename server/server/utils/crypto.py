# Standard library
import hashlib
import secrets
# Third party libraries
import tracers.function

# Local libraries
import server.utils.aio
import server.utils.encodings


@tracers.function.trace()
@server.utils.aio.to_async
def get_hash(*, string: str, salt: str = '') -> str:
    algorithm: hashlib.shake_256 = hashlib.shake_256()
    algorithm.update(salt.encode('utf-8'))
    algorithm.update(string.encode('utf-8'))

    return algorithm.hexdigest(1024)


@tracers.function.trace()
@server.utils.aio.to_async
def get_salt(*, num_of_bytes: int = 64) -> str:
    return server.utils.encodings.encode_bytes(
        get_salt_bytes(num_of_bytes=num_of_bytes),
    )


@tracers.function.trace()
@server.utils.aio.to_async
def get_salt_bytes(*, num_of_bytes: int = 64) -> bytes:
    return secrets.token_bytes(num_of_bytes)
