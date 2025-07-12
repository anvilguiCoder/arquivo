from werkzeug.security import generate_password_hash
from database import get_db
import os

def inicializar_admin():
    # Obtém a senha segura do ambiente (.env ou Render)
    senha_admin = os.environ.get("ADMIN_SENHA", "admin123")
    senha_hash = generate_password_hash(senha_admin)

    db = get_db()
    cursor = db.cursor()

    # Verifica se já existe um admin cadastrado
    cursor.execute("SELECT * FROM usuarios WHERE usuario = ?", ("admin",))
    if cursor.fetchone() is None:
        cursor.execute("""
            INSERT INTO usuarios (usuario, senha, tipo)
            VALUES (?, ?, ?)
        """, ("admin", senha_hash, "admin"))
        db.commit()
        print("Usuário admin criado.")
    else:
        print("Usuário admin já existe.")
