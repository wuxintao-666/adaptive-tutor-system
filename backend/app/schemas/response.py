# backend/app/schemas/response.py
from pydantic import BaseModel
from typing import Generic, TypeVar, Optional

T = TypeVar('T')
class StandardResponse(BaseModel, Generic[T]):
    code: int = 200
    message: str = 'success'
    data: Optional[T]