from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.models.product import Product
from app.schemas.product import ProductCreate, ProductUpdate, ProductResponse
from app.redis_client import redis_client
import json

router = APIRouter(prefix="/products", tags=["Products"])

def product_cache_key(product_id: int):
    return f"product:{product_id}"

def products_list_cache_key(category: Optional[str]):
    return f"products:{category or 'all'}"


@router.get("/", response_model=list[ProductResponse])
def list_products(category: Optional[str] = None, db: Session = Depends(get_db)):
    cache_key = products_list_cache_key(category)
    cached = redis_client.get(cache_key)
    if cached:
        print(f"✅ Cache HIT: {cache_key}")
        return json.loads(cached)

    print(f"❌ Cache MISS: {cache_key}")
    query = db.query(Product)
    if category:
        query = query.filter(Product.category == category)
    products = query.all()

    serialized = json.dumps([{
        "id": p.id,
        "name": p.name,
        "description": p.description,
        "price": p.price,
        "stock": p.stock,
        "category": p.category,
        "created_at": str(p.created_at),
        "updated_at": str(p.updated_at) if p.updated_at else None
    } for p in products])
    redis_client.setex(cache_key, 60, serialized)
    return products


@router.get("/{product_id}", response_model=ProductResponse)
def get_product(product_id: int, db: Session = Depends(get_db)):
    cache_key = product_cache_key(product_id)
    cached = redis_client.get(cache_key)
    if cached:
        print(f"✅ Cache HIT: {cache_key}")
        return json.loads(cached)

    print(f"❌ Cache MISS: {cache_key}")
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    serialized = json.dumps({
        "id": product.id,
        "name": product.name,
        "description": product.description,
        "price": product.price,
        "stock": product.stock,
        "category": product.category,
        "created_at": str(product.created_at),
        "updated_at": str(product.updated_at) if product.updated_at else None
    })
    redis_client.setex(cache_key, 300, serialized)
    return product


@router.post("/", response_model=ProductResponse, status_code=201)
def create_product(product: ProductCreate, db: Session = Depends(get_db)):
    db_product = Product(**product.dict())
    db.add(db_product)
    db.commit()
    db.refresh(db_product)

    keys = redis_client.keys("products:*")
    if keys:
        redis_client.delete(*keys)
        print(f"🗑️ Invalidated cache keys: {keys}")

    return db_product


@router.patch("/{product_id}", response_model=ProductResponse)
def update_product(product_id: int, updates: ProductUpdate, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    for field, value in updates.dict(exclude_unset=True).items():
        setattr(product, field, value)

    db.commit()
    db.refresh(product)

    redis_client.delete(product_cache_key(product_id))
    keys = redis_client.keys("products:*")
    if keys:
        redis_client.delete(*keys)

    return product


@router.delete("/{product_id}", status_code=204)
def delete_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    db.delete(product)
    db.commit()

    redis_client.delete(product_cache_key(product_id))
    keys = redis_client.keys("products:*")
    if keys:
        redis_client.delete(*keys)

    return None


@router.patch("/{product_id}/stock")
def update_stock(product_id: int, quantity: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    if product.stock + quantity < 0:
        raise HTTPException(status_code=400, detail=f"Insufficient stock. Current stock: {product.stock}")

    product.stock += quantity
    db.commit()

    redis_client.delete(product_cache_key(product_id))
    return {"product_id": product_id, "new_stock": product.stock}