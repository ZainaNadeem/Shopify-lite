from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.product import Product
from app.schemas.cart import CartItem, CartResponse, CartItemResponse
from app.redis_client import redis_client
import json

router = APIRouter(prefix="/cart", tags=["Cart"])

def cart_key(user_id: str) -> str:
    return f"cart:{user_id}"


@router.get("/{user_id}", response_model=CartResponse)
def get_cart(user_id: str):
    """Get the current cart for a user"""
    cart_data = redis_client.get(cart_key(user_id))
    cart = json.loads(cart_data) if cart_data else {}

    items = []
    total = 0.0
    for item in cart.values():
        subtotal = item["price"] * item["quantity"]
        total += subtotal
        items.append(CartItemResponse(
            product_id=item["product_id"],
            name=item["name"],
            price=item["price"],
            quantity=item["quantity"],
            subtotal=round(subtotal, 2)
        ))

    return CartResponse(user_id=user_id, items=items, total=round(total, 2))


@router.post("/{user_id}/items", response_model=CartResponse)
def add_to_cart(user_id: str, item: CartItem, db: Session = Depends(get_db)):
    """Add a product to the cart"""
    # Verify product exists
    product = db.query(Product).filter(Product.id == item.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # Check stock
    if product.stock < item.quantity:
        raise HTTPException(
            status_code=400,
            detail=f"Not enough stock. Available: {product.stock}"
        )

    # Get existing cart
    cart_data = redis_client.get(cart_key(user_id))
    cart = json.loads(cart_data) if cart_data else {}

    # Add or update item
    product_key = str(item.product_id)
    if product_key in cart:
        cart[product_key]["quantity"] += item.quantity
    else:
        cart[product_key] = {
            "product_id": item.product_id,
            "name": product.name,
            "price": product.price,
            "quantity": item.quantity
        }

    # Save to Redis with 24hr expiry
    redis_client.setex(cart_key(user_id), 86400, json.dumps(cart))
    print(f"🛒 Added {item.quantity}x {product.name} to cart for user {user_id}")

    return get_cart(user_id)


@router.delete("/{user_id}/items/{product_id}", response_model=CartResponse)
def remove_from_cart(user_id: str, product_id: int):
    """Remove a specific item from the cart"""
    cart_data = redis_client.get(cart_key(user_id))
    if not cart_data:
        raise HTTPException(status_code=404, detail="Cart not found")

    cart = json.loads(cart_data)
    product_key = str(product_id)

    if product_key not in cart:
        raise HTTPException(status_code=404, detail="Item not in cart")

    del cart[product_key]
    redis_client.setex(cart_key(user_id), 86400, json.dumps(cart))

    return get_cart(user_id)


@router.delete("/{user_id}", status_code=204)
def clear_cart(user_id: str):
    """Clear the entire cart"""
    redis_client.delete(cart_key(user_id))
    return None