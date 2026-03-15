from app.database import engine, Base
from app.models.product import Product

# This creates the products table in PostgreSQL
Base.metadata.create_all(bind=engine)
print("✅ Database connected and tables created!")