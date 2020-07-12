def encode(string: str) -> str:
    return encode_bytes(string.encode('utf-8'))


def encode_bytes(bytestring: bytes) -> str:
    return bytestring.hex().lower()


def decode(hexstr: str) -> str:
    return decode_bytes(hexstr).decode('utf-8')


def decode_bytes(hexstr: str) -> bytes:
    return bytes.fromhex(hexstr)
