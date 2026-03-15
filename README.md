# Shopify Lite API

A production-ready backend API for e-commerce featuring CRUD product management, real-time inventory tracking, high-performance Redis caching, and Stripe-powered payments.
<img width="1423" height="812" alt="Image" src="https://github.com/user-attachments/assets/b343a118-4c9b-4216-b34d-736d86dbe577" />

<img width="1423" height="353" alt="Image" src="https://github.com/user-attachments/assets/c48244f4-ed35-4850-af60-f8369d029cc8" />

## Tech Stack

Backend Framework
- Python
- FastAPI

Database
- PostgreSQL
- SQLAlchemy ORM

Caching
- Redis

Payments
- Stripe API

Infrastructure
- Docker
- Docker Compose

## Features
- Product catalog with CRUD operations
- Inventory tracking with stock management
- Shopping cart (Redis-powered, 24hr TTL)
- Stripe checkout + webhook order confirmation
- Redis caching with 50ms response times (60% query reduction)

## Flow
1. User adds items to cart
2. Cart is stored in Redis with 24hr TTL
3. Checkout endpoint retrieves cart
4. Backend calculates order total
5. Stripe PaymentIntent is created
6. Client completes payment using client_secret
7. Stripe sends webhook to confirm payment

## Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Start services
docker-compose up -d

# Run server
uvicorn app.main:app --reload
```

## API Endpoints
- `GET/POST /products/` — List and create products
- `GET/PATCH/DELETE /products/{id}` — Manage single product
- `PATCH /products/{id}/stock` — Update inventory
- `GET /cart/{user_id}` — View cart
- `POST /cart/{user_id}/items` — Add to cart
- `DELETE /cart/{user_id}` — Clear cart
- `POST /payments/checkout/{user_id}` — Stripe checkout
- `POST /payments/webhook` — Stripe webhook

## API Documentation

Once the server is running, interactive API docs are available at:

http://127.0.0.1:8000/docs
