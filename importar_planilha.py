import sqlite3
import openpyxl

# Instale antes: pip install openpyxl
wb = openpyxl.load_workbook('Estoque.xlsx')
ws = wb['PRODUTOS']

conn = sqlite3.connect('estoque.db')
conn.row_factory = sqlite3.Row

# Garante que as colunas extras existem
try:
    conn.execute('ALTER TABLE produtos ADD COLUMN fornecedor TEXT DEFAULT ""')
except: pass
try:
    conn.execute('ALTER TABLE produtos ADD COLUMN unidade TEXT DEFAULT ""')
except: pass
try:
    conn.execute('ALTER TABLE produtos ADD COLUMN categoria TEXT DEFAULT ""')
except: pass
try:
    conn.execute('ALTER TABLE produtos ADD COLUMN marca TEXT DEFAULT ""')
except: pass
try:
    conn.execute('ALTER TABLE produtos ADD COLUMN descricao TEXT DEFAULT ""')
except: pass

importados = 0
ignorados = 0

for row in ws.iter_rows(min_row=2, values_only=True):
    codigo    = str(row[0]).strip() if row[0] else None
    nome      = str(row[1]).strip() if row[1] else None
    fornecedor= str(row[2]).strip() if row[2] else ''
    unidade   = str(row[3]).strip() if row[3] else ''
    categoria = str(row[4]).strip() if row[4] else ''
    marca     = str(row[5]).strip() if row[5] else ''
    localizacao=str(row[6]).strip() if row[6] else ''
    descricao = str(row[7]).strip() if row[7] else ''

    if not nome or nome == 'None':
        ignorados += 1
        continue

    # Formata código
    try:
        codigo_fmt = str(int(float(codigo))) if codigo and codigo != 'None' else ''
    except:
        codigo_fmt = str(codigo) if codigo else ''

    conn.execute('''
        INSERT OR IGNORE INTO produtos 
        (nome, codigo, localizacao, estoque_atual, estoque_minimo, fornecedor, unidade, categoria, marca, descricao)
        VALUES (?, ?, ?, 0, 0, ?, ?, ?, ?, ?)
    ''', (nome, codigo_fmt, localizacao, fornecedor, unidade, categoria, marca, descricao))
    importados += 1

conn.commit()
conn.close()
print(f"✅ {importados} produtos importados!")
print(f"⚠ {ignorados} linhas ignoradas (sem nome)")