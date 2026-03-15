import stripe
import os
import json
from fastapi import APIRouter, Request, HTTPException, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.product import Product
from app.redis_client import redis_client
from dotenv import load_dotenv

load_dotenv()

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
router = APIRouter(prefix="/payments", tags=["Payments"])


@router.post("/checkout/{user_id}")
def create_checkout(user_id: str, db: Session = Depends(get_db)):
    """Create a Stripe PaymentIntent for the user's cart"""

    # Get cart from Redis
    cart_data = redis_client.get(f"cart:{user_id}")
    if not cart_data:
        raise HTTPException(status_code=400, detail="Cart is empty")

    cart = json.loads(cart_data)
    if not cart:
        raise HTTPException(status_code=400, detail="Cart is empty")

    # Calculate total in cents (Stripe uses cents)
    total_cents = int(sum(
        item["price"] * item["quantity"] for item in cart.values()
    ) * 100)

    # Create PaymentIntent with Stripe
    intent = stripe.PaymentIntent.create(
        amount=total_cents,
        currency="usd",
        metadata={"user_id": user_id},
    )

    return {
        "client_secret": intent.client_secret,
        "payment_intent_id": intent.id,
        "amount": total_cents / 100,
        "currency": "usd"
    }


@router.post("/webhook")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    """Handle Stripe webhook events"""
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    # Verify webhook came from Stripe
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, os.getenv("STRIPE_WEBHOOK_SECRET")
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    # Handle successful payment
    if event["type"] == "payment_intent.succeeded":
        intent = event["data"]["object"]
        user_id = intent["metadata"]["user_id"]

        print(f"✅ Payment succeeded for user {user_id}")

        # Deduct stock from DB
        cart_data = redis_client.get(f"cart:{user_id}")
        if cart_data:
            cart = json.loads(cart_data)
            for product_id, item in cart.items():
                product = db.query(Product).filter(
                    Product.id == int(product_id)
                ).first()
                if product:
                    product.stock -= item["quantity"]
                    print(f"📦 Deducted {item['quantity']} from {product.name}")
            db.commit()

        # Clear the cart
        redis_client.delete(f"cart:{user_id}")
        print(f"🗑️ Cleared cart for user {user_id}")

    elif event["type"] == "payment_intent.payment_failed":
        intent = event["data"]["object"]
        print(f"❌ Payment failed for user {intent['metadata'].get('user_id')}")

    return {"status": "ok"}


@router.get("/status/{payment_intent_id}")
def payment_status(payment_intent_id: str):
    """Check the status of a payment"""
    try:
        intent = stripe.PaymentIntent.retrieve(payment_intent_id)
        return {
            "id": intent.id,
            "status": intent.status,
            "amount": intent.amount / 100,
            "currency": intent.currency
        }
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=400, detail=str(e))