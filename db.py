import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

def get_db():
    """
    Retorna uma conexão com o banco de dados PostgreSQL.
    """
    if not DATABASE_URL:
        raise ValueError("DATABASE_URL não está definida nas variáveis de ambiente.")

    try:
        conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
        return conn
    except Exception as e:
        print(f"[ERRO] Falha ao conectar ao PostgreSQL: {e}")
        raise
