from pydantic import BaseModel, validator
from typing import Optional
from datetime import datetime

class ProductCreate(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    stock: int
    category: str

    @validator('price')
    def price_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError('Price must be greater than 0')
        return round(v, 2)

    @validator('stock')
    def stock_must_be_positive(cls, v):
        if v < 0:
            raise ValueError('Stock cannot be negative')
        return v

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    stock: Optional[int] = None
    category: Optional[str] = None

class ProductResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    price: float
    stock: int
    category: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True