import time
from collections.abc import Callable
from functools import wraps
from typing import Any, TypeVar, cast

F = TypeVar('F', bound=Callable[..., Any])

def retry(num_retries: int = 3, sleep_between: float = 1) -> Callable[[F], F]:
    """
    Decorator to retry a function on failure.
    
    :param num_retries: Number of retry attempts
    :type num_retries: int
    :param sleep_between: Seconds to sleep between retries
    :type sleep_between: float
    
    :return: Decorated function
    :rtype: Callable[[F], F]
    """
    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            attempts = 0
            while attempts < num_retries:
                try:
                    return func(*args, **kwargs)
                except Exception:
                    attempts += 1
                    if attempts == num_retries:
                        raise
                    time.sleep(sleep_between)
                    print(f"Retrying... Attempt {attempts + 1}/{num_retries}")
        return cast(F, wrapper)
    return decorator