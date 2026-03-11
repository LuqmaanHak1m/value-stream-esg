import psycopg2
import os

from dotenv import load_dotenv


load_dotenv()

def get_db_connection():
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL not found in environment")
    return psycopg2.connect(database_url)