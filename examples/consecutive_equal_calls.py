# Local libraries
import time

# Third party libraries
from tracers.function import trace


@trace()
def function_a():
    for _ in range(100):
        function_b()


@trace()
def function_b():
    time.sleep(0.001)


if __name__ == '__main__':
    function_a()
    time.sleep(1)
