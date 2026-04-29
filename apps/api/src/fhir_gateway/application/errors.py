class ApplicationValidationError(Exception):
    def __init__(self, field: str, message: str) -> None:
        super().__init__(f"{field}: {message}")
        self.field = field
        self.message = message


class ApplicationNotFoundError(Exception):
    def __init__(self, resource: str, identifier: str) -> None:
        message = f"{resource} not found: {identifier}"
        super().__init__(message)
        self.resource = resource
        self.identifier = identifier
        self.message = message
