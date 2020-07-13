# Local libraries
import asyncio

# Third party libraries
from tracers.function import call, trace


@trace()
async def function_a():
    await call(asyncio.sleep, 0.1)
    await function_b()


@trace()
async def function_b():
    await call(asyncio.sleep, 0.1)
    await function_c()
    await call(asyncio.sleep, 0.1)
    await function_d()
    await call(asyncio.sleep, 0.1)
    await function_e()


@trace()
async def function_c():
    await call(asyncio.sleep, 0.1)
    await function_d()


@trace()
async def function_d():
    await call(asyncio.sleep, 0.1)


@trace()
async def function_e():
    await call(asyncio.sleep, 0.1)


async def main():
    await asyncio.gather(*[
        asyncio.create_task(function_a()),
        asyncio.create_task(function_b()),
    ])
    await asyncio.sleep(1.0)


if __name__ == '__main__':
    asyncio.run(main())
