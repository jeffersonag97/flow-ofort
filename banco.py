import sqlite3

def criar_banco():
    conexao = sqlite3.connect('estoque.db')
    cursor = conexao.cursor()

    # 1. PRODUTOS (O cadastro mestre)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS produtos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            codigo TEXT,
            localizacao TEXT,
            estoque_atual INTEGER DEFAULT 0,
            estoque_minimo INTEGER DEFAULT 0,
            preco_unitario REAL DEFAULT 0.0
        )
    ''')

    # Garante que a coluna codigo exista em versões antigas do esquema
    cursor.execute("PRAGMA table_info(produtos)")
    colunas = [row[1] for row in cursor.fetchall()]
    if 'codigo' not in colunas:
        cursor.execute('ALTER TABLE produtos ADD COLUMN codigo TEXT')

    # 2. FUNCIONARIOS (Quem retira ou quem entrega)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS funcionarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            cargo TEXT
        )
    ''')

    # 3. MOVIMENTACOES (Onde registramos Entrada e Saída)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS movimentacoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            produto_id INTEGER,
            funcionario_id INTEGER,
            quantidade INTEGER NOT NULL,
            tipo TEXT NOT NULL, -- Aqui vai "ENTRADA" ou "SAIDA"
            data_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            protocolo_papel TEXT, -- Para você anotar o número do papel se quiser
            FOREIGN KEY (produto_id) REFERENCES produtos (id),
            FOREIGN KEY (funcionario_id) REFERENCES funcionarios (id)
        )
    ''')

    # 4. INVENTÁRIOS e ITENS DE INVENTÁRIO (para as telas correspondentes)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS inventarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            responsavel TEXT NOT NULL,
            observacao TEXT,
            status TEXT NOT NULL,
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS inventario_itens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            inventario_id INTEGER,
            produto_id INTEGER,
            estoque_sistema INTEGER DEFAULT 0,
            estoque_contado INTEGER DEFAULT 0,
            diferenca INTEGER DEFAULT 0,
            ajustado INTEGER DEFAULT 0,
            FOREIGN KEY (inventario_id) REFERENCES inventarios (id),
            FOREIGN KEY (produto_id) REFERENCES produtos (id)
        )
    ''')

    conexao.commit()
    conexao.close()
    print("Banco de dados atualizado com sucesso! Agora suporta cadastro completo e inventários.")

if __name__ == "__main__":
    criar_banco()