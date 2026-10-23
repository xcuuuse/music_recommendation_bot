class RecordNotFoundError(Exception):
    def __init__(self, message: str):
        super().__init__(message)

class RecordAlreadyExists(Exception):
    def __init__(self, message: str):
        super().__init__(message)

