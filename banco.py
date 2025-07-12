import sqlite3
import os

caminho_banco = os.path.join("dados", "banco.sqlite")
conn = sqlite3.connect(caminho_banco)
cursor = conn.cursor()

# Tabela de alunos
cursor.execute('''
CREATE TABLE IF NOT EXISTS alunos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    data_nascimento TEXT NOT NULL,
    cpf TEXT NOT NULL UNIQUE,
    numero_caixa TEXT NOT NULL
)
''')

# Tabela de usuários
cursor.execute('''
CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario TEXT NOT NULL UNIQUE,
    senha TEXT NOT NULL,
    tipo TEXT NOT NULL CHECK (tipo IN ('admin', 'comum'))
)
''')

# Inserir usuário admin padrão, se não existir
cursor.execute("SELECT * FROM usuarios WHERE usuario = 'admin'")
if cursor.fetchone() is None:
    cursor.execute("INSERT INTO usuarios (usuario, senha, tipo) VALUES (?, ?, ?)",
                   ('admin', 'admin123', 'admin'))
    print("Usuário admin criado (usuario: admin, senha: admin123)")

conn.commit()
conn.close()