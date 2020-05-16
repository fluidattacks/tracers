# Local libraries
import time
import asyncio

# Third party libraries
from tracers.function import trace


@trace
async def function_a():
    await trace(asyncio.sleep)(0.1)
    trace(time.sleep)(0.5)
    await function_b()


@trace
async def function_b():
    await trace(asyncio.sleep)(0.1)
    await function_c()
    trace(time.sleep)(2)
    await trace(asyncio.sleep)(0.1)
    await function_d()
    await trace(asyncio.sleep)(0.1)
    await function_e()


@trace
async def function_c():
    await trace(asyncio.sleep)(0.1)
    trace(time.sleep)(0.5)
    await function_d()


@trace
async def function_d():
    await trace(asyncio.sleep)(0.1)


@trace
async def function_e():
    await trace(asyncio.sleep)(0.1)


if __name__ == '__main__':
    asyncio.run(function_a())
