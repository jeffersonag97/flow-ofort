import sqlite3
from werkzeug.security import generate_password_hash

conn = sqlite3.connect('estoque.db')

try:
    conn.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            login TEXT UNIQUE NOT NULL,
            senha TEXT NOT NULL,
            nivel TEXT DEFAULT 'operador'
        )
    ''')

    # Cria o usuário administrador padrão
    senha_hash = generate_password_hash('admin123')
    conn.execute('''
        INSERT OR IGNORE INTO usuarios (nome, login, senha, nivel)
        VALUES (?, ?, ?, ?)
    ''', ('Administrador', 'admin', senha_hash, 'admin'))

    conn.commit()
    print("✅ Tabela de usuários criada!")
    print("👤 Login: ofort")
    print("🔑 Senha: ofort@2026")

except Exception as e:
    print(f"Erro: {e}")

conn.close()