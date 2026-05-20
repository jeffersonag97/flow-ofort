import sqlite3

conn = sqlite3.connect('estoque.db')

try:
    # Tabela de cabeçalho do inventário (cada vez que você faz um inventário)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS inventarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            responsavel TEXT,
            status TEXT DEFAULT 'ABERTO',
            observacao TEXT
        )
    ''')

    # Tabela de itens contados em cada inventário
    conn.execute('''
        CREATE TABLE IF NOT EXISTS inventario_itens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            inventario_id INTEGER,
            produto_id INTEGER,
            estoque_sistema INTEGER,
            estoque_contado INTEGER,
            diferenca INTEGER,
            ajustado INTEGER DEFAULT 0,
            FOREIGN KEY (inventario_id) REFERENCES inventarios(id),
            FOREIGN KEY (produto_id) REFERENCES produtos(id)
        )
    ''')

    conn.commit()
    print("✅ Tabelas de inventário criadas com sucesso!")

except Exception as e:
    print(f"Erro: {e}")

conn.close()