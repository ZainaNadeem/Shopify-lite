from fastapi import FastAPI
from app.database import Base, engine
from app.routers import products, cart, payments
from app.redis_client import ping_redis

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Shopify Lite API",
    description="Product catalog with Redis caching and Stripe payments",
    version="1.0.0"
)

@app.on_event("startup")
def startup():
    ping_redis()

app.include_router(products.router)
app.include_router(cart.router)
app.include_router(payments.router)

@app.get("/health")
def health():
    return {"status": "ok"}