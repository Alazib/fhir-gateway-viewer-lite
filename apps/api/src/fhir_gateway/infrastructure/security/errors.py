class TokenVerificationError(Exception):
    def __init__(self, message: str = "Token verification failed.") -> None:
        self.message = message
        super().__init__(message)


class TokenVerifierConfigurationError(Exception):
    def __init__(self, message: str = "Token verifier is not correctly configured.") -> None:
        self.message = message
        super().__init__(message)
