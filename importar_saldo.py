import sqlite3
import openpyxl

# data_only=True pega os valores calculados, não as fórmulas
wb = openpyxl.load_workbook('Estoque.xlsx', data_only=True)
ws = wb['ESTOQUE ATUAL']

conn = sqlite3.connect('estoque.db')

atualizados = 0
nao_encontrados = 0

for row in ws.iter_rows(min_row=2, values_only=True):
    codigo = row[0]
    saldo = row[6]  # Coluna G

    if not codigo:
        continue

    # Formata o código removendo .0 e zeros à esquerda
    try:
        codigo_fmt = str(int(float(str(codigo))))
    except:
        codigo_fmt = str(codigo).strip()

    # Formata o saldo
    try:
        saldo_int = int(float(saldo)) if saldo is not None else 0
    except:
        saldo_int = 0

    # Tenta sem zeros à esquerda
    result = conn.execute(
        'UPDATE produtos SET estoque_atual = ? WHERE codigo = ?',
        (saldo_int, codigo_fmt)
    )

    if result.rowcount > 0:
        atualizados += 1
        continue

    # Tenta com zeros à esquerda (9 dígitos)
    codigo_com_zero = codigo_fmt.zfill(9)
    result = conn.execute(
        'UPDATE produtos SET estoque_atual = ? WHERE codigo = ?',
        (saldo_int, codigo_com_zero)
    )

    if result.rowcount > 0:
        atualizados += 1
    else:
        nao_encontrados += 1
        print(f"Não encontrado: {codigo_fmt}")

conn.commit()
conn.close()
print(f"\n✅ {atualizados} produtos atualizados!")
print(f"⚠ {nao_encontrados} não encontrados.")