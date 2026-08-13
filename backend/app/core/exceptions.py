from fastapi import HTTPException, status


class DomainError(HTTPException):
    """Excepción base de dominio. Genera respuestas consistentes con la sección 50."""

    def __init__(self, code: str, message: str, status_code: int = status.HTTP_400_BAD_REQUEST):
        super().__init__(
            status_code=status_code,
            detail={"success": False, "error": {"code": code, "message": message}},
        )


class InvalidCredentials(DomainError):
    def __init__(self):
        super().__init__(
            code="INVALID_CREDENTIALS",
            message="Correo o contraseña incorrectos",
            status_code=status.HTTP_401_UNAUTHORIZED,
        )


class InactiveUser(DomainError):
    def __init__(self):
        super().__init__(
            code="INACTIVE_USER",
            message="El usuario está desactivado",
            status_code=status.HTTP_403_FORBIDDEN,
        )


class InvalidToken(DomainError):
    def __init__(self, detail: str = "Token inválido o expirado"):
        super().__init__(
            code="INVALID_TOKEN", message=detail, status_code=status.HTTP_401_UNAUTHORIZED
        )


class Forbidden(DomainError):
    def __init__(self, message: str = "No tienes permiso para esta acción"):
        super().__init__(code="FORBIDDEN", message=message, status_code=status.HTTP_403_FORBIDDEN)
