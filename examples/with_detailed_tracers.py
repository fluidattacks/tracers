import time
from dateutil.parser import parse
from tracers.function import call, trace


@trace()
def example():
    call(time.sleep, 2.0)
    your_business_logic('Sat Oct 11')


@trace()
def your_business_logic(date: str):
    call(parse, date)
    call(time.sleep, 1.0)


example()
time.sleep(1)
