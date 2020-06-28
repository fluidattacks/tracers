import time
from dateutil.parser import parse
from tracers.function import trace


@trace()
def example():
    time.sleep(2.0)
    your_business_logic('Sat Oct 11')


@trace()
def your_business_logic(date: str):
    parse(date)
    time.sleep(1.0)


example()
