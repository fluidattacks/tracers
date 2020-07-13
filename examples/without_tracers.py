import time
from dateutil.parser import parse


def example():
    time.sleep(2.0)
    your_business_logic('Sat Oct 11')


def your_business_logic(date: str):
    parse(date)
    time.sleep(1.0)


example()
time.sleep(1)
