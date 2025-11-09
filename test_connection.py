import os
from dotenv import load_dotenv
import psycopg2
import requests

load_dotenv()

# Test PostgreSQL Connection
def test_postgres():
    try:
        conn = psycopg2.connect(
            host=os.getenv('DATABASE_HOST'),
            database=os.getenv('DATABASE_NAME'),
            user=os.getenv('DATABASE_USER'),
            password=os.getenv('DATABASE_PASSWORD')
        )
        print("✅ PostgreSQL Connection: SUCCESS")
        conn.close()
    except Exception as e:
        print(f"❌ PostgreSQL Connection: FAILED - {e}")

if __name__ == "__main__":
    test_postgres()