from pydantic import BaseModel

class CartItem(BaseModel):
    product_id: int
    quantity: int

class CartItemResponse(BaseModel):
    product_id: int
    name: str
    price: float
    quantity: int
    subtotal: float

class CartResponse(BaseModel):
    user_id: str
    items: list[CartItemResponse]
    total: float