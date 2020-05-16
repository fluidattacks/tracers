import time
from dateutil.parser import parse
from tracers.function import trace


@trace
def example():
    trace(time.sleep)(2.0)
    your_business_logic('Sat Oct 11')


@trace
def your_business_logic(date: str):
    trace(parse)(date)
    trace(time.sleep)(1.0)


example()
