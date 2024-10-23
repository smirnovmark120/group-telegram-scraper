import time
from functools import wraps

# Define a threshold for "too long" in seconds (e.g., 0.1 seconds)
TIME_THRESHOLD = 0.01

def timer_decorator(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.perf_counter()  # More precise timing
        result = func(*args, **kwargs)
        end_time = time.perf_counter()
        elapsed_time = end_time - start_time

        # Only print if function took longer than the threshold
        if elapsed_time > TIME_THRESHOLD:
            print(f"⚠️ Function '{func.__name__}' took {elapsed_time:.6f} seconds (too long)")

        return result
    return wrapper

# Define the TimerMeta metaclass
class TimerMeta(type):
    def __init__(cls, name, bases, dct):
        super().__init__(name, bases, dct)
        for attr_name, attr_value in dct.items():
            if callable(attr_value) and not attr_name.startswith("__"):
                # Decorate each method with the timer_decorator
                setattr(cls, attr_name, timer_decorator(attr_value))
