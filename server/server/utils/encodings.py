# Third party libraries
import tracers.function

# Local libraries
import server.utils.aio


@tracers.function.trace()
async def encode(string: str) -> str:
    result = await server.utils.aio.unblock(string.encode, 'utf-8')

    return await encode_bytes(result)


@tracers.function.trace()
async def encode_bytes(bytestring: bytes) -> str:
    return await server.utils.aio.unblock(bytestring.hex)


@tracers.function.trace()
async def decode(hexstr: str) -> str:
    result = await decode_bytes(hexstr)

    return await server.utils.aio.unblock(result.decode, 'utf-8')


@tracers.function.trace()
async def decode_bytes(hexstr: str) -> bytes:
    return await server.utils.aio.unblock(bytes.fromhex, hexstr)
