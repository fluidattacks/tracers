# Local libraries
import time

# Third party libraries
from tracers.function import call, trace


@trace()
def function_a():
    call(time.sleep, 0.1)
    function_b()


@trace()
def function_b():
    call(time.sleep, 0.1)
    function_c()
    call(time.sleep, 0.1)
    function_d()
    call(time.sleep, 0.1)
    function_e()


@trace()
def function_c():
    call(time.sleep, 0.1)
    function_d()


@trace()
def function_d():
    call(time.sleep, 0.1)


@trace()
def function_e():
    call(time.sleep, 0.1)


def main():
    function_a()
    function_b()


if __name__ == '__main__':
    main()
