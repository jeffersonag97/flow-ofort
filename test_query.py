import sqlite3
conn = sqlite3.connect('estoque.db')
conn.row_factory = sqlite3.Row
try:
    inv = conn.execute('SELECT * FROM inventarios WHERE id = 5').fetchone()
    print(f"Inventário encontrado: {dict(inv) if inv else 'NÃO'}")
    
    itens = conn.execute('''
        SELECT ii.id, ii.estoque_sistema, ii.estoque_contado, ii.diferenca, ii.ajustado,
               p.nome as produto, p.codigo, p.localizacao
        FROM inventario_itens ii
        JOIN produtos p ON ii.produto_id = p.id
        WHERE ii.inventario_id = 5
        ORDER BY p.localizacao, p.nome
    ''').fetchall()
    print(f"Itens encontrados: {len(itens)}")
    for item in itens[:2]:
        print(dict(item))
except Exception as e:
    print(f"ERRO: {e}")
    import traceback
    traceback.print_exc()
finally:
    conn.close()
