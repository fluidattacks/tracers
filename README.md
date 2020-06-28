# Table of contents

- [Table of contents](#table-of-contents)
- [Project description](#project-description)
  * [Key Features](#key-features)
- [Quick Introduction](#quick-introduction)
- [Installation](#installation)
- [Examples](#examples)

# Project description

**Tracers** is an Open-Source **APM** (Application monitoring) project
that offers you minimal overhead wrappers for profiling your code execution flow

```
🛈  Finished transaction: 3.81 seconds

     # Timestamp                Net              Total    Call Chain

     1     0.00s     0.00s [  0.0%]     3.81s [100.0%]    ✓ async function_a
     2     0.00s     0.10s [  2.6%]     0.10s [  2.6%]    ¦   ✓ async asyncio.tasks.sleep
     3     0.10s     0.50s [ 13.1%]     0.50s [ 13.1%]    ¦   ✓ time.sleep
     4     0.60s     0.00s [  0.0%]     3.21s [ 84.2%]    ¦   ✓ async function_b
     5     0.60s     0.10s [  2.6%]     0.10s [  2.6%]    ¦   ¦   ✓ async asyncio.tasks.sleep
     6     0.70s     0.00s [  0.0%]     0.70s [ 18.4%]    ¦   ¦   ✓ async function_c
     7     0.70s     0.10s [  2.6%]     0.10s [  2.6%]    ¦   ¦   ¦   ✓ async asyncio.tasks.sleep
     8     0.80s     0.50s [ 13.1%]     0.50s [ 13.1%]    ¦   ¦   ¦   ✓ time.sleep
     9     1.31s     0.00s [  0.0%]     0.10s [  2.7%]    ¦   ¦   ¦   ✓ async function_d
    10     1.31s     0.10s [  2.6%]     0.10s [  2.6%]    ¦   ¦   ¦   ¦   ✓ async asyncio.tasks.sleep
    11     1.41s     2.00s [ 52.5%]     2.00s [ 52.5%]    ¦   ¦   ✓ time.sleep
    12     3.41s     0.10s [  2.7%]     0.10s [  2.7%]    ¦   ¦   ✓ async asyncio.tasks.sleep
    13     3.51s     0.00s [  0.0%]     0.10s [  2.7%]    ¦   ¦   ✓ async function_d
    14     3.51s     0.10s [  2.7%]     0.10s [  2.7%]    ¦   ¦   ¦   ✓ async asyncio.tasks.sleep
    15     3.61s     0.10s [  2.7%]     0.10s [  2.7%]    ¦   ¦   ✓ async asyncio.tasks.sleep
    16     3.71s     0.00s [  0.0%]     0.10s [  2.7%]    ¦   ¦   ✓ async function_e
    17     3.71s     0.10s [  2.7%]     0.10s [  2.7%]    ¦   ¦   ¦   ✓ async asyncio.tasks.sleep

           Count                Net              Total    Function

               3     3.00s [ 78.7%]     3.00s [ 78.7%]    ✓ time.sleep
               8     0.81s [ 21.2%]     0.81s [ 21.2%]    ✓ async asyncio.tasks.sleep
               1     0.00s [  0.0%]     3.21s [ 84.2%]    ✓ async function_b
               1     0.00s [  0.0%]     0.70s [ 18.4%]    ✓ async function_c
               1     0.00s [  0.0%]     3.81s [100.0%]    ✓ async function_a
               2     0.00s [  0.0%]     0.20s [  5.3%]    ✓ async function_d
               1     0.00s [  0.0%]     0.10s [  2.7%]    ✓ async function_e

  Some blocks (skews) occurred in the event loop ¹

  #    Timestamp     Delay

     0     1.40s     2.00s
     1     0.09s     0.50s
     2     0.80s     0.50s

  ¹ Consider reviewing them carefully to improve the overall system throughput
```

## Key Features

- Allows you to instrument any **function** or **statement**
  on **your own code** or any **third party library**
- Handles [**asynchronous**](https://docs.python.org/3/library/asyncio.html) code
  **out-of-the box**, no config required
- Exposes a **high-level API**:
  - A decorator: `@trace`, to instrument functions
    - Example:
      ```
      @trace
      def any_function(*args, **kwargs):
          pass

      @trace
      async def other_function(*args, **kwargs):
          pass
      ```
  - A function: `call` to instrument code in-line
    - Example:
      ```
      call(any_function, *args, **kwargs)
      await call(other_function, *args, **kwargs)
      ```
  - Sync/async cases are handled internally
  - `call` and `@trace` are equivalent, you can choose the one that fits you best
- It's **Thread-safe**, **Async-safe**, **Process-safe** and **Context-safe**
  - You'll get accurate results in any scenario
- Introduces **minimal overhead** and it's **easy to deploy**!
  - It's a pure python implementation based on
   [contextvars](https://docs.python.org/3/library/contextvars.html) and
   [decorators](https://docs.python.org/3/glossary.html#term-decorator).
   Your code runs as fast as if you were not profiling it
- It's easy to pin-point performance problems:
  - Gives you the total execution time in seconds and **%**
  - Allows you to identify points in time where your **async** event loop got blocked
- Made with love by nerds, for humans :heart:

# Quick Introduction

Let's start with a very basic example:

```py
import time
from dateutil.parser import parse


def example():
    time.sleep(2.0)
    your_business_logic('Sat Oct 11')


def your_business_logic(date: str):
    parse(date)
    time.sleep(1.0)


example()
```

Tracing its flow and gathering profiling information is a matter of
decorating your functions:

```diff
--- a/examples/without_tracers.py
+++ b/examples/with_tracers.py
@@ -1,15 +1,18 @@
 import time
 from dateutil.parser import parse
+from tracers.function import trace


+@trace()
 def example():
     time.sleep(2.0)
     your_business_logic('Sat Oct 11')


+@trace()
 def your_business_logic(date: str):
     parse(date)
     time.sleep(1.0)


 example()
```

If you run it, all the functions you decorated will be traced
and you'll have metrics of the execution flow:

```
🛈  Finished transaction: 3.00 seconds

     # Timestamp                Net              Total    Call Chain

     1     0.00s     2.00s [ 66.7%]     3.00s [100.0%]    ✓ example
     2     2.00s     1.00s [ 33.3%]     1.00s [ 33.3%]    ¦   ✓ your_business_logic

           Count                Net              Total    Function

               1     2.00s [ 66.7%]     3.00s [100.0%]    ✓ example
               1     1.00s [ 33.3%]     1.00s [ 33.3%]    ✓ your_business_logic
```

From the output you can conclude:
- executing function *example* took a total of *3.0* seconds to complete
- function *example* takes *66.7%* of the execution time
- function *example encloses *100%* of your code time
- function *example* called function: *your_business_logic*
- function *your_business_logic* took *1.0* seconds out of the *3.0* seconds
  the function *example* needed to complete
- function *your_business_logic* represents *33.3%* of your execution time

Tracing code is not limited to your own code.
You can trace any **callable object** including **third party packages**,
**Python's standard library**, and almost anything

The level of detail is up to you!


```diff
--- a/examples/with_tracers.py
+++ b/examples/with_detailed_tracers.py
@@ -1,18 +1,18 @@
 import time
 from dateutil.parser import parse
-from tracers.function import trace
+from tracers.function import call, trace


 @trace()
 def example():
-    time.sleep(2.0)
+    call(time.sleep, 2.0)
     your_business_logic('Sat Oct 11')


 @trace()
 def your_business_logic(date: str):
-    parse(date)
-    time.sleep(1.0)
+    call(parse, date)
+    call(time.sleep, 1.0)


 example()
```

```

🛈  Finished transaction: 3.00 seconds

     # Timestamp                Net              Total    Call Chain

     1     0.00s     0.00s [  0.0%]     3.00s [100.0%]    ✓ example
     2     0.00s     2.00s [ 66.6%]     2.00s [ 66.6%]    ¦   ✓ time.sleep
     3     2.00s     0.00s [  0.0%]     1.00s [ 33.4%]    ¦   ✓ your_business_logic
     4     2.00s     0.00s [  0.0%]     0.00s [  0.0%]    ¦   ¦   ✓ dateutil.parser._parser.parse
     5     2.00s     1.00s [ 33.3%]     1.00s [ 33.3%]    ¦   ¦   ✓ time.sleep

           Count                Net              Total    Function

               2     3.00s [100.0%]     3.00s [100.0%]    ✓ time.sleep
               1     0.00s [  0.0%]     0.00s [  0.0%]    ✓ dateutil.parser._parser.parse
               1     0.00s [  0.0%]     1.00s [ 33.4%]    ✓ your_business_logic
               1     0.00s [  0.0%]     3.00s [100.0%]    ✓ example

```

# Installation

We are hosted on **PyPI**: https://pypi.org/project/tracers

Just run: `pip install tracers`
or use the package manager you like the most

# Examples

Check them out in the
[examples](https://github.com/kamadorueda/tracers/tree/master/examples)
folder
