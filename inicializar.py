import os
import psycopg2
from psycopg2 import sql
from werkzeug.security import generate_password_hash
from db import get_db

def criar_tabelas():
    """
    Cria as tabelas 'usuarios' e 'alunos' no banco de dados PostgreSQL, se ainda não existirem.
    """
    conn = get_db()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS usuarios (
                id SERIAL PRIMARY KEY,
                usuario VARCHAR(255) UNIQUE NOT NULL,
                senha TEXT NOT NULL,
                tipo VARCHAR(10) NOT NULL CHECK(tipo IN ('admin', 'comum'))
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS alunos (
                id SERIAL PRIMARY KEY,
                nome VARCHAR(255) NOT NULL,
                data_nascimento VARCHAR(10) NOT NULL,
                cpf VARCHAR(14) UNIQUE NOT NULL,
                numero_caixa VARCHAR(50) NOT NULL
            )
        """)

        conn.commit()
        print("Tabelas criadas com sucesso.")
    except Exception as e:
        print(f"[ERRO] Falha ao criar tabelas: {e}")
    finally:
        conn.close()


def inicializar_admin():
    """
    Cria o usuário admin no banco PostgreSQL se ainda não existir.
    """
    usuario_admin = (os.environ.get("ADMIN_USER") or "admin").strip()
    senha_admin = (os.environ.get("ADMIN_PASSWORD") or "admin123").strip()
    senha_hash = generate_password_hash(senha_admin)

    conn = get_db()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT 1 FROM usuarios WHERE usuario = %s", (usuario_admin,))
        if cursor.fetchone() is None:
            cursor.execute("""
                INSERT INTO usuarios (usuario, senha, tipo)
                VALUES (%s, %s, %s)
            """, (usuario_admin, senha_hash, "admin"))
            conn.commit()
            print(f"Usuário admin '{usuario_admin}' criado.")
        else:
            print(f"Usuário admin '{usuario_admin}' já existe.")
    except Exception as e:
        print(f"[ERRO] Falha ao inicializar admin: {e}")
    finally:
        conn.close()


if __name__ == "__main__":
    criar_tabelas()
    inicializar_admin()
