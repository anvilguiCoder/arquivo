import sqlite3

# Caminho para o banco de dados
CAMINHO_BANCO = 'dados/banco.sqlite'

# Conecta ao banco
conn = sqlite3.connect(CAMINHO_BANCO)
cursor = conn.cursor()

# Solicita o nome do usuário a ser deletado
usuario_a_deletar = input("Digite o nome do usuário a ser excluído: ").strip()

# Verifica se o usuário existe
cursor.execute("SELECT usuario, tipo FROM usuarios WHERE usuario = ?", (usuario_a_deletar,))
resultado = cursor.fetchone()

if resultado:
    print(f"\nUsuário encontrado: {resultado[0]} (tipo: {resultado[1]})")
    confirmar = input("Deseja realmente excluir este usuário? (s/n): ").lower()

    if confirmar == 's':
        cursor.execute("DELETE FROM usuarios WHERE usuario = ?", (usuario_a_deletar,))
        conn.commit()
        print(f"✅ Usuário '{usuario_a_deletar}' excluído com sucesso.")
    else:
        print("❌ Exclusão cancelada.")
else:
    print("⚠️ Usuário não encontrado.")

# Fecha a conexão
conn.close()
