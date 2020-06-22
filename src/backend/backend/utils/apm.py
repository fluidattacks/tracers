# Third party libraries
import tracers.function


def trace(function_name: str = ''):
    return tracers.function.trace(
        do_trace=True,
        function_name=function_name,
    )
