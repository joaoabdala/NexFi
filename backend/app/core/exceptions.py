class NexFiError(Exception):
    """Base para erros de domínio, traduzidos para HTTP pelos handlers globais."""

    status_code: int = 400

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class NotFoundError(NexFiError):
    status_code = 404


class ValidationError(NexFiError):
    status_code = 422


class ConflictError(NexFiError):
    status_code = 409


class UnauthorizedError(NexFiError):
    status_code = 401


class ForbiddenError(NexFiError):
    status_code = 403


class TooManyRequestsError(NexFiError):
    status_code = 429
