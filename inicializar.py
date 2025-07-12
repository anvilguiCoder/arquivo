import os
from werkzeug.security import generate_password_hash
from db import get_db

def inicializar_admin():
    # Obtém a senha segura do ambiente (.env ou Render)
    senha_admin = os.environ.get("ADMIN_SENHA", "admin123").strip()
    senha_hash = generate_password_hash(senha_admin)

    conn = get_db()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT 1 FROM usuarios WHERE usuario = ?", ("admin",))
        if cursor.fetchone() is None:
            cursor.execute("""
                INSERT INTO usuarios (usuario, senha, tipo)
                VALUES (?, ?, ?)
            """, ("admin", senha_hash, "admin"))
            conn.commit()
            print("Usuário admin criado.")
        else:
            print("Usuário admin já existe.")
    except Exception as e:
        print(f"[ERRO] Falha ao inicializar admin: {e}")
    finally:
        conn.close()
