# Standard library
import hashlib
import secrets

# Local libraries
import server.utils.encodings


def get_hash(*, string: str, salt: str = '') -> str:
    algorithm = hashlib.shake_256()
    algorithm.update(salt.encode('utf-8'))
    algorithm.update(string.encode('utf-8'))

    return algorithm.hexdigest()


def get_salt(*, num_of_bytes: int = 64) -> str:
    return server.utils.encodings.encode_bytes(
        get_salt_bytes(num_of_bytes=num_of_bytes),
    )


def get_salt_bytes(*, num_of_bytes: int = 64) -> bytes:
    return secrets.token_bytes(num_of_bytes)
