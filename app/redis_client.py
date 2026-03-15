import redis
import os
from dotenv import load_dotenv

load_dotenv()

redis_client = redis.Redis.from_url(
    os.getenv("REDIS_URL"),
    decode_responses=True
)

def ping_redis():
    try:
        redis_client.ping()
        print("✅ Redis connected!")
    except Exception as e:
        print(f"❌ Redis connection failed: {e}")