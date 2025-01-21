import time
from functools import wraps

def retry(num_retries=3, sleep_between=1):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            attempts = 0
            while attempts < num_retries:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    attempts += 1
                    if attempts == num_retries:
                        raise
                    time.sleep(sleep_between)
                    print(f"Retrying... Attempt {attempts + 1}/{num_retries}")
        return wrapper
    return decorator