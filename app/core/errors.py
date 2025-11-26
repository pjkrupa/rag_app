from functools import wraps

# a wrapper that handles errors and logs them.
def handle_api_errors(default):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger = kwargs.get("logger")
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if logger:
                    logger.error(f"Error in {func.__name__}: {e}", exc_info=True)
                else:
                    raise e
            return default
        return wrapper
    return decorator