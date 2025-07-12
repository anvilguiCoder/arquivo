import sqlite3
import os
from dotenv import load_dotenv

load_dotenv()

# Caminho padrão para o banco de dados
CAMINHO_BANCO = os.getenv("DB_PATH", os.path.join("dados", "banco.sqlite"))

# Cria a pasta onde o banco será salvo, se não existir
os.makedirs(os.path.dirname(CAMINHO_BANCO), exist_ok=True)

def get_db():
    """
    Retorna uma conexão com o banco de dados SQLite.
    """
    try:
        conn = sqlite3.connect(CAMINHO_BANCO)
        return conn
    except sqlite3.Error as e:
        print(f"[ERRO] Falha ao conectar ao banco: {e}")
        raise
