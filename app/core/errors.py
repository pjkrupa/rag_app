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

class ConfigurationsError(Exception):
    pass

class MetadataFilterError(Exception):
    pass