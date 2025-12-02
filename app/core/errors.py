from functools import wraps

class UserNotFoundError(Exception):
    """Raised when a user is not found in the database"""
    pass

class UserAlreadyExistsError(Exception):
    """Raised when user tries to create a name that already exists"""
    pass

class ChatNotFoundError(Exception):
    """Raised when a chat is not found in the database"""
    pass

class ToolParseError(Exception):
    pass

class LlmCallFailedError(Exception):
    pass

class RagClientFailedError(Exception):
    pass

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