from pydantic import BaseModel


class ApiError(BaseModel):
    code: str
    message: str
    field: str | None = None
    resource: str | None = None
    identifier: str | None = None


class ApiErrorResponse(BaseModel):
    error: ApiError
