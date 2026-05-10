import sqlite3

conn = sqlite3.connect('estoque.db')

try:
    conn.execute('ALTER TABLE produtos ADD COLUMN codigo TEXT DEFAULT ""')
    conn.commit()
    print("✅ Coluna 'codigo' adicionada!")
except Exception as e:
    print(f"Aviso: {e}")

conn.close()