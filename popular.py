import sqlite3

conn = sqlite3.connect('estoque.db')
# Adicionando alguns itens de teste
conn.execute("INSERT INTO produtos (nome, localizacao, estoque_atual) VALUES ('Papel A4', 'Rua A', 100)")
conn.execute("INSERT INTO produtos (nome, localizacao, estoque_atual) VALUES ('Cabo HDMI', 'Rua B', 20)")
conn.execute("INSERT INTO funcionarios (nome) VALUES ('Jefferson Germano')")
conn.execute("INSERT INTO funcionarios (nome) VALUES ('Colaborador Teste')")

conn.commit()
conn.close()
print("Dados de teste inseridos!")