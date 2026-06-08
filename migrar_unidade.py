import sqlite3

conn = sqlite3.connect('estoque.db')

try:
    conn.execute('ALTER TABLE produtos ADD COLUMN unidade TEXT DEFAULT "UN"')
    conn.commit()
    print("✅ Coluna unidade adicionada!")
except Exception as e:
    print(f"Aviso: {e}")

conn.close()
