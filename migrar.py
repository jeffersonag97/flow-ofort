import sqlite3

conn = sqlite3.connect('estoque.db')

try:
    conn.execute('ALTER TABLE produtos ADD COLUMN estoque_minimo INTEGER DEFAULT 0')
    conn.commit()
    print("✅ Coluna 'estoque_minimo' adicionada com sucesso!")
except Exception as e:
    print(f"Aviso: {e}")

conn.close()