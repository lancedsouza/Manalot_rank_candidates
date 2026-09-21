import os 
from sqlalchemy import create_engine
from dotenv import load_dotenv
from sqlalchemy.orm import declarative_base,sessionmaker
import logging
import psycopg2

logger = logging.getLogger(__name__)


load_dotenv()

DATABASE_URL=os.getenv("DATABASE_URL")
if not DATABASE_URL:
    logger.error("Database url not found in environmental varaiiables")
    raise ValueError("Database url not found")
engine=create_engine(DATABASE_URL,pool_pre_ping=True)

Base=declarative_base()

SessionLocal=sessionmaker(
    bind=engine
    
)

