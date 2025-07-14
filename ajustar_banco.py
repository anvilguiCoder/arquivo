import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()  # Carrega variáveis do .env

try:
    conn = psycopg2.connect(os.getenv("DATABASE_URL"))
    cursor = conn.cursor()

    cursor.execute("ALTER TABLE usuarios ADD COLUMN nome VARCHAR(100);")
    conn.commit()

    print("✅ Coluna 'nome' adicionada com sucesso.")
except psycopg2.errors.DuplicateColumn:
    print("⚠️ A coluna 'nome' já existe no banco.")
except Exception as e:
    print("❌ Erro ao ajustar banco:", e)
finally:
    if conn:
        cursor.close()
        conn.close()
