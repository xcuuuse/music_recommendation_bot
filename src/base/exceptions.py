class RecordNotFoundError(Exception):
    def __init__(self, message: str):
        super().__init__(message)

class RecordAlreadyExists(Exception):
    def __init__(self, message: str):
        super().__init__(message)

class UserNotFoundError(Exception):
    def __init__(self, message: str):
        super().__init__(message)

class NothingToRecommendError(Exception):
    def __init__(self, message: str):
        super().__init__(message)

class AlbumNotFoundError(Exception):
    def __init__(self, message: str):
        super().__init__(message)