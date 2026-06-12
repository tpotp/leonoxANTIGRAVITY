from fastapi import HTTPException, status

class SmartWMSException(HTTPException):
    def __init__(self, status_code: int, detail: str):
        super().__init__(status_code=status_code, detail=detail)

class NotFoundException(SmartWMSException):
    def __init__(self, detail: str = "Recurso no encontrado"):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)

class BadRequestException(SmartWMSException):
    def __init__(self, detail: str = "Solicitud incorrecta"):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)
