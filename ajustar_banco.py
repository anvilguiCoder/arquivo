import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()  # Carrega variáveis do .env

try:
    conn = psycopg2.connect(os.getenv("DATABASE_URL"))
    cursor = conn.cursor()

    # Adicionar coluna nome
    try:
        cursor.execute("ALTER TABLE usuarios ADD COLUMN nome VARCHAR(100);")
        print("✅ Coluna 'nome' adicionada com sucesso.")
    except psycopg2.errors.DuplicateColumn:
        print("⚠️ A coluna 'nome' já existe no banco.")
        conn.rollback()

    # Adicionar coluna email
    try:
        cursor.execute("ALTER TABLE usuarios ADD COLUMN email VARCHAR(100);")
        print("✅ Coluna 'email' adicionada com sucesso.")
    except psycopg2.errors.DuplicateColumn:
        print("⚠️ A coluna 'email' já existe no banco.")
        conn.rollback()

    # Adicionar coluna status
    try:
        cursor.execute("ALTER TABLE usuarios ADD COLUMN status VARCHAR(20) DEFAULT 'ativo';")
        print("✅ Coluna 'status' adicionada com sucesso.")
    except psycopg2.errors.DuplicateColumn:
        print("⚠️ A coluna 'status' já existe no banco.")
        conn.rollback()
        
    # Adicionar coluna senha_hash
    try:
        cursor.execute("ALTER TABLE usuarios ADD COLUMN senha_hash VARCHAR(255);")
        print("✅ Coluna 'senha_hash' adicionada com sucesso.")
    except psycopg2.errors.DuplicateColumn:
        print("⚠️ A coluna 'senha_hash' já existe no banco.")
        conn.rollback()
        

    conn.commit()

except Exception as e:
    print("❌ Erro ao ajustar banco:", e)
finally:
    if conn:
        cursor.close()
        conn.close()
