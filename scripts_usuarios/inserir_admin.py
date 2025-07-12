import sqlite3
from werkzeug.security import generate_password_hash

# Conexão com o banco
conn = sqlite3.connect('dados/banco.sqlite')
cursor = conn.cursor()

# Dados do novo admin
usuario = ''
senha_plana = ''  # Você pode trocar por outra senha segura
senha_hash = generate_password_hash(senha_plana)
tipo = 'admin'

# Inserir usuário admin
try:
    cursor.execute('INSERT INTO usuarios (usuario, senha, tipo) VALUES (?, ?, ?)',
                   (usuario, senha_hash, tipo))
    conn.commit()
    print(f"Usuário admin '{usuario}' inserido com sucesso!")
except sqlite3.IntegrityError:
    print(f"Usuário '{usuario}' já existe.")
finally:
    conn.close()
