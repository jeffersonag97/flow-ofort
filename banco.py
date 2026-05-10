import sqlite3

def criar_banco():
    conexao = sqlite3.connect('estoque.db')
    cursor = conexao.cursor()

    # 1. PRODUTOS (O cadastro mestre)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS produtos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            localizacao TEXT,
            estoque_atual INTEGER DEFAULT 0,
            estoque_minimo INTEGER DEFAULT 0,
            preco_unitario REAL DEFAULT 0.0
        )
    ''')

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


    conexao.commit()
    conexao.close()
    print("Banco de dados atualizado com Sucesso! Agora suporta Entrada e Saída.")

if __name__ == "__main__":
    criar_banco()