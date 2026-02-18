from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Try to import redis for the website
REDIS_INCLUDED = True
try:
	import redis
except:
	REDIS_INCLUDED = False

from . import SSP_DB_FILE

#Create engine and session to be imported by all connections
engine = create_engine("sqlite:///" + SSP_DB_FILE, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Define Redis Connection and verify the Redis service is available via `ping()`.
if REDIS_INCLUDED:
	RedisDB = redis.StrictRedis(host='localhost', port=6379, db=0)
	try:
		RedisDB.ping()
		print("Successfully connected to Redis Cache")
	except:
		RedisDB = None
		print("Failed to connect to Redis, setting RedisDB to None and will not use redis caching")
# If Redis is not available, then `RedisDB` is set to `None`.
else:
	RedisDB = None
