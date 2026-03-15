from app.schemas.product import ProductCreate, ProductUpdate

# Test valid product
p = ProductCreate(name="Laptop", price=999.99, stock=50, category="Electronics")
print("✅ Valid product:", p)

# Test invalid price
try:
    bad = ProductCreate(name="Laptop", price=-10, stock=50, category="Electronics")
except Exception as e:
    print("✅ Caught bad price:", e)

# Test invalid stock
try:
    bad = ProductCreate(name="Laptop", price=999.99, stock=-5, category="Electronics")
except Exception as e:
    print("✅ Caught bad stock:", e)

# Test partial update
u = ProductUpdate(price=899.99)
print("✅ Partial update:", u)