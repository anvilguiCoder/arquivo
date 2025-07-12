import sqlite3
from werkzeug.security import generate_password_hash

# Conecta ao banco
conn = sqlite3.connect('dados/banco.sqlite')
cursor = conn.cursor()

# Dados do novo usuário
usuario = ''
senha_plana = ''
senha_hash = generate_password_hash(senha_plana)
tipo = 'comum'

# Inserção
cursor.execute('INSERT INTO usuarios (usuario, senha, tipo) VALUES (?, ?, ?)',
               (usuario, senha_hash, tipo))

conn.commit()
conn.close()

print(f"Usuário '{usuario}' inserido com sucesso.")
