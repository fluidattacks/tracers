# Local libraries
import time

# Third party libraries
from tracers.function import trace


@trace
def function_a():
    trace(time.sleep)(0.1)
    function_b()


@trace
def function_b():
    trace(time.sleep)(0.1)
    function_c()
    trace(time.sleep)(0.1)
    function_d()
    trace(time.sleep)(0.1)
    function_e()


@trace
def function_c():
    trace(time.sleep)(0.1)
    function_d()


@trace
def function_d():
    trace(time.sleep)(0.1)


@trace
def function_e():
    trace(time.sleep)(0.1)


def main():
    function_a()
    function_b()


if __name__ == '__main__':
    main()
