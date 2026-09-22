
import os, redis
url = os.getenv("REDIS_URL", "redis://localhost:6380")
r = redis.Redis.from_url(url, decode_responses=True)
r.flushall()
print("Redis flushed at", url)
