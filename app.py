from flask import Flask, render_template, request, redirect, url_for, flash # type: ignore
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = 'sua_chave_secreta_aqui'  # Necessário para usar flash messages

# Cache para alertas (atualiza a cada 5 minutos)
_alertas_cache = {'count': 0, 'timestamp': None}

@contextmanager
def conectar():
    """Context manager para gerenciar conexões com o banco de dados"""
    conn = sqlite3.connect('estoque.db')
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def get_alertas_count(usar_cache=True):
    """Retorna contagem de alertas com suporte a cache"""
    global _alertas_cache
    
    # Verifica se cache é válido (menos de 5 minutos)
    if usar_cache and _alertas_cache['timestamp']:
        tempo_decorrido = datetime.now() - _alertas_cache['timestamp']
        if tempo_decorrido < timedelta(minutes=5):
            return _alertas_cache['count']
    
    try:
        with conectar() as conn:
            count = conn.execute('''
                SELECT COUNT(*) FROM produtos 
                WHERE estoque_atual <= estoque_minimo AND estoque_minimo > 0
            ''').fetchone()[0]
            
            # Atualiza cache
            _alertas_cache['count'] = count
            _alertas_cache['timestamp'] = datetime.now()
            
            return count
    except Exception as e:
        print(f"Erro ao contar alertas: {e}")
        return 0

@app.route('/')
def index():
    try:
        with conectar() as conn:
            produtos = conn.execute('SELECT * FROM produtos').fetchall()
            funcionarios = conn.execute('SELECT * FROM funcionarios').fetchall()
            
            historico = conn.execute('''
                SELECT m.id, m.tipo, p.nome as produto, m.quantidade, f.nome as quem, m.data_hora 
                FROM movimentacoes m
                JOIN produtos p ON m.produto_id = p.id
                JOIN funcionarios f ON m.funcionario_id = f.id
                ORDER BY m.id DESC LIMIT 10
            ''').fetchall()
        
        return render_template('index.html', 
                               produtos=produtos, 
                               funcionarios=funcionarios, 
                               saidas=historico, 
                               alertas_count=get_alertas_count())
    except Exception as e:
        flash(f'❌ Erro ao carregar dados: {str(e)}', 'danger')
        return render_template('index.html', 
                               produtos=[], 
                               funcionarios=[], 
                               saidas=[], 
                               alertas_count=0)


@app.route('/movimentar', methods=['POST'])
def movimentar():
    try:
        prod_id = request.form.get('produto_id')
        func_id = request.form.get('funcionario_id')
        tipo = request.form.get('tipo')  # "ENTRADA" ou "SAIDA"
        
        # Validação de entrada
        if not prod_id or not func_id or not tipo:
            flash('❌ Todos os campos são obrigatórios!', 'danger')
            return redirect(url_for('index'))
        
        try:
            qtd = int(request.form.get('quantidade', 0))
        except ValueError:
            flash('❌ Quantidade deve ser um número inteiro!', 'danger')
            return redirect(url_for('index'))
        
        if qtd <= 0:
            flash('❌ Quantidade deve ser maior que zero!', 'danger')
            return redirect(url_for('index'))

        with conectar() as conn:
            # Validação de SAIDA
            if tipo == 'SAIDA':
                produto = conn.execute(
                    'SELECT estoque_atual, nome FROM produtos WHERE id = ?', 
                    (prod_id,)
                ).fetchone()
                
                if not produto:
                    flash('❌ Produto não encontrado!', 'danger')
                    return redirect(url_for('index'))
                
                if produto['estoque_atual'] < qtd:
                    flash(
                        f"❌ Estoque insuficiente de '{produto['nome']}'! "
                        f"Disponível: {produto['estoque_atual']} | Solicitado: {qtd}", 
                        'danger'
                    )
                    return redirect(url_for('index'))
            
            # Atualiza estoque
            if tipo == 'ENTRADA':
                conn.execute(
                    'UPDATE produtos SET estoque_atual = estoque_atual + ? WHERE id = ?', 
                    (qtd, prod_id)
                )
            else:
                conn.execute(
                    'UPDATE produtos SET estoque_atual = estoque_atual - ? WHERE id = ?', 
                    (qtd, prod_id)
                )
            
            # Registra movimentação
            conn.execute('''
                INSERT INTO movimentacoes (produto_id, funcionario_id, quantidade, tipo)
                VALUES (?, ?, ?, ?)
            ''', (prod_id, func_id, qtd, tipo))
        
        # Invalida cache de alertas
        _alertas_cache['timestamp'] = None
        
        flash(f'✅ {tipo} registrada com sucesso!', 'success')
        return redirect(url_for('index'))
    
    except Exception as e:
        flash(f'❌ Erro ao processar: {str(e)}', 'danger')
        return redirect(url_for('index'))
@app.route('/cadastro')
def cadastro():
    try:
        with conectar() as conn:
            produtos = conn.execute('SELECT * FROM produtos').fetchall()
            funcionarios = conn.execute('SELECT * FROM funcionarios').fetchall()
        
        return render_template('cadastro.html', 
                               produtos=produtos, 
                               funcionarios=funcionarios, 
                               alertas_count=get_alertas_count())
    except Exception as e:
        flash(f'❌ Erro ao carregar dados: {str(e)}', 'danger')
        return render_template('cadastro.html', 
                               produtos=[], 
                               funcionarios=[], 
                               alertas_count=0)

@app.route('/cadastrar_produto', methods=['POST'])
def cadastrar_produto():
    try:
        nome = request.form.get('nome', '').strip()
        codigo = request.form.get('codigo', '').strip()
        
        if not nome or not codigo:
            flash('❌ Nome e código são obrigatórios!', 'danger')
            return redirect(url_for('cadastro'))
        
        localizacao = request.form.get('localizacao', '').strip()
        
        try:
            estoque_inicial = int(request.form.get('estoque_inicial', 0) or 0)
            estoque_minimo = int(request.form.get('estoque_minimo', 0) or 0)
        except ValueError:
            flash('❌ Estoque deve ser um número inteiro!', 'danger')
            return redirect(url_for('cadastro'))
        
        if estoque_inicial < 0 or estoque_minimo < 0:
            flash('❌ Estoque não pode ser negativo!', 'danger')
            return redirect(url_for('cadastro'))

        with conectar() as conn:
            conn.execute('''
                INSERT INTO produtos (nome, codigo, localizacao, estoque_atual, estoque_minimo)
                VALUES (?, ?, ?, ?, ?)
            ''', (nome, codigo, localizacao, estoque_inicial, estoque_minimo))
        
        _alertas_cache['timestamp'] = None
        flash(f'✅ Produto "{nome}" cadastrado com sucesso!', 'success')
        return redirect(url_for('cadastro'))
    
    except Exception as e:
        flash(f'❌ Erro ao cadastrar produto: {str(e)}', 'danger')
        return redirect(url_for('cadastro'))

@app.route('/cadastrar_funcionario', methods=['POST'])
def cadastrar_funcionario():
    try:
        nome = request.form.get('nome', '').strip()
        cargo = request.form.get('cargo', '').strip()
        
        if not nome:
            flash('❌ Nome é obrigatório!', 'danger')
            return redirect(url_for('cadastro'))

        with conectar() as conn:
            conn.execute(
                'INSERT INTO funcionarios (nome, cargo) VALUES (?, ?)', 
                (nome, cargo)
            )
        
        flash(f'✅ Funcionário "{nome}" cadastrado com sucesso!', 'success')
        return redirect(url_for('cadastro'))
    
    except Exception as e:
        flash(f'❌ Erro ao cadastrar funcionário: {str(e)}', 'danger')
        return redirect(url_for('cadastro'))

@app.route('/excluir_produto/<int:id>')
def excluir_produto(id):
    try:
        with conectar() as conn:
            produto = conn.execute('SELECT nome FROM produtos WHERE id = ?', (id,)).fetchone()
            
            if not produto:
                flash('❌ Produto não encontrado!', 'danger')
                return redirect(url_for('cadastro'))
            
            conn.execute('DELETE FROM produtos WHERE id = ?', (id,))
        
        _alertas_cache['timestamp'] = None
        flash(f'✅ Produto "{produto["nome"]}" excluído com sucesso!', 'success')
        return redirect(url_for('cadastro'))
    
    except Exception as e:
        flash(f'❌ Erro ao excluir produto: {str(e)}', 'danger')
        return redirect(url_for('cadastro'))

@app.route('/excluir_funcionario/<int:id>')
def excluir_funcionario(id):
    try:
        with conectar() as conn:
            funcionario = conn.execute('SELECT nome FROM funcionarios WHERE id = ?', (id,)).fetchone()
            
            if not funcionario:
                flash('❌ Funcionário não encontrado!', 'danger')
                return redirect(url_for('cadastro'))
            
            conn.execute('DELETE FROM funcionarios WHERE id = ?', (id,))
        
        flash(f'✅ Funcionário "{funcionario["nome"]}" excluído com sucesso!', 'success')
        return redirect(url_for('cadastro'))
    
    except Exception as e:
        flash(f'❌ Erro ao excluir funcionário: {str(e)}', 'danger')
        return redirect(url_for('cadastro'))
@app.route('/historico')
def historico():
    try:
        data_inicio = request.args.get('data_inicio', '')
        data_fim = request.args.get('data_fim', '')
        funcionario_id = request.args.get('funcionario_id', '')
        tipo = request.args.get('tipo', '')

        query = '''
            SELECT m.id, m.tipo, p.nome as produto, p.codigo, m.quantidade, 
                   f.nome as funcionario, m.data_hora
            FROM movimentacoes m
            JOIN produtos p ON m.produto_id = p.id
            JOIN funcionarios f ON m.funcionario_id = f.id
            WHERE 1=1
        '''
        params = []

        if data_inicio:
            query += ' AND DATE(m.data_hora) >= ?'
            params.append(data_inicio)
        if data_fim:
            query += ' AND DATE(m.data_hora) <= ?'
            params.append(data_fim)
        if funcionario_id:
            query += ' AND m.funcionario_id = ?'
            params.append(funcionario_id)
        if tipo:
            query += ' AND m.tipo = ?'
            params.append(tipo)

        query += ' ORDER BY m.id DESC'

        with conectar() as conn:
            movimentacoes = conn.execute(query, params).fetchall()
            funcionarios = conn.execute('SELECT * FROM funcionarios').fetchall()
        
        total_entradas = sum(m['quantidade'] for m in movimentacoes if m['tipo'] == 'ENTRADA')
        total_saidas = sum(m['quantidade'] for m in movimentacoes if m['tipo'] == 'SAIDA')

        return render_template('historico.html', 
                               movimentacoes=movimentacoes,
                               funcionarios=funcionarios,
                               total_entradas=total_entradas,
                               total_saidas=total_saidas,
                               filtros={
                                   'data_inicio': data_inicio,
                                   'data_fim': data_fim,
                                   'funcionario_id': funcionario_id,
                                   'tipo': tipo,
                               },
                               alertas_count=get_alertas_count())
    
    except Exception as e:
        flash(f'❌ Erro ao carregar histórico: {str(e)}', 'danger')
        return render_template('historico.html', 
                               movimentacoes=[],
                               funcionarios=[],
                               total_entradas=0,
                               total_saidas=0,
                               filtros={},
                               alertas_count=0)
@app.route('/alertas')
def alertas():
    try:
        with conectar() as conn:
            produtos_baixos = conn.execute('''
                SELECT * FROM produtos 
                WHERE estoque_atual <= estoque_minimo AND estoque_minimo > 0
                ORDER BY estoque_atual ASC
            ''').fetchall()
        
        return render_template('alertas.html', 
                               produtos=produtos_baixos,
                               alertas_count=get_alertas_count())
    except Exception as e:
        flash(f'❌ Erro ao carregar alertas: {str(e)}', 'danger')
        return render_template('alertas.html', 
                               produtos=[],
                               alertas_count=0)
@app.route('/editar_produto/<int:id>')
def editar_produto(id):
    try:
        with conectar() as conn:
            produto = conn.execute('SELECT * FROM produtos WHERE id = ?', (id,)).fetchone()
        
        if not produto:
            flash('❌ Produto não encontrado!', 'danger')
            return redirect(url_for('cadastro'))
        
        return render_template('editar_produto.html', 
                               produto=produto,
                               alertas_count=get_alertas_count())
    except Exception as e:
        flash(f'❌ Erro: {str(e)}', 'danger')
        return redirect(url_for('cadastro'))

@app.route('/salvar_produto/<int:id>', methods=['POST'])
def salvar_produto(id):
    try:
        nome = request.form.get('nome', '').strip()
        codigo = request.form.get('codigo', '').strip()
        localizacao = request.form.get('localizacao', '').strip()
        
        try:
            estoque_minimo = int(request.form.get('estoque_minimo', 0) or 0)
        except ValueError:
            flash('❌ Estoque mínimo deve ser um número!', 'danger')
            return redirect(url_for('editar_produto', id=id))
        
        if not nome:
            flash('❌ Nome é obrigatório!', 'danger')
            return redirect(url_for('editar_produto', id=id))

        with conectar() as conn:
            conn.execute('''
                UPDATE produtos 
                SET nome = ?, codigo = ?, localizacao = ?, estoque_minimo = ?
                WHERE id = ?
            ''', (nome, codigo, localizacao, estoque_minimo, id))
        
        _alertas_cache['timestamp'] = None
        flash(f'✅ Produto "{nome}" atualizado com sucesso!', 'success')
        return redirect(url_for('cadastro'))
    
    except Exception as e:
        flash(f'❌ Erro ao salvar: {str(e)}', 'danger')
        return redirect(url_for('editar_produto', id=id))
    
@app.route('/comprovante/<int:id>')
def comprovante(id):
    try:
        with conectar() as conn:
            movimentacao = conn.execute('''
                SELECT m.id, m.tipo, m.quantidade, m.data_hora,
                       p.nome as produto, p.codigo as codigo,
                       p.localizacao as localizacao,
                       f.nome as funcionario, f.cargo as cargo
                FROM movimentacoes m
                JOIN produtos p ON m.produto_id = p.id
                JOIN funcionarios f ON m.funcionario_id = f.id
                WHERE m.id = ?
            ''', (id,)).fetchone()
        
        if not movimentacao:
            flash('❌ Movimentação não encontrada!', 'danger')
            return redirect(url_for('historico'))
        
        return render_template('comprovante.html', m=movimentacao)
    
    except Exception as e:
        flash(f'❌ Erro: {str(e)}', 'danger')
        return redirect(url_for('historico'))


@app.route('/inventario')
def inventario():
    try:
        with conectar() as conn:
            inventarios = conn.execute('''
                SELECT * FROM inventarios ORDER BY id DESC
            ''').fetchall()
        
        return render_template('inventario.html',
                               inventarios=inventarios,
                               alertas_count=get_alertas_count())
    except Exception as e:
        flash(f'❌ Erro: {str(e)}', 'danger')
        return redirect(url_for('index'))


@app.route('/inventario/novo', methods=['POST'])
def novo_inventario():
    try:
        responsavel = request.form.get('responsavel', '').strip()
        observacao = request.form.get('observacao', '').strip()

        if not responsavel:
            flash('❌ Informe o responsável!', 'danger')
            return redirect(url_for('inventario'))

        with conectar() as conn:
            cursor = conn.execute('''
                INSERT INTO inventarios (responsavel, observacao, status)
                VALUES (?, ?, 'ABERTO')
            ''', (responsavel, observacao))
            inventario_id = cursor.lastrowid

            # Já carrega todos os produtos com saldo atual do sistema
            produtos = conn.execute('SELECT * FROM produtos').fetchall()
            for p in produtos:
                conn.execute('''
                    INSERT INTO inventario_itens 
                    (inventario_id, produto_id, estoque_sistema, estoque_contado, diferenca)
                    VALUES (?, ?, ?, 0, 0)
                ''', (inventario_id, p['id'], p['estoque_atual']))

        flash('✅ Inventário iniciado com sucesso!', 'success')
        return redirect(url_for('contar_inventario', id=inventario_id))

    except Exception as e:
        flash(f'❌ Erro: {str(e)}', 'danger')
        return redirect(url_for('inventario'))


@app.route('/inventario/<int:id>/contar')
def contar_inventario(id):
    try:
        with conectar() as conn:
            inv = conn.execute('SELECT * FROM inventarios WHERE id = ?', (id,)).fetchone()
            itens = conn.execute('''
                SELECT ii.id, ii.estoque_sistema, ii.estoque_contado, ii.diferenca, ii.ajustado,
                       p.nome as produto, p.codigo, p.localizacao
                FROM inventario_itens ii
                JOIN produtos p ON ii.produto_id = p.id
                WHERE ii.inventario_id = ?
                ORDER BY p.localizacao, p.nome
            ''', (id,)).fetchall()

        print(f"DEBUG: inv={inv}, itens count={len(itens) if itens else 0}")
        
        if not inv:
            flash(f'❌ Inventário {id} não encontrado!', 'danger')
            return redirect(url_for('inventario'))

        if not itens:
            print(f"DEBUG: Sem itens para inventário {id}")
            flash(f'❌ Inventário {id} não tem itens! Produtos cadastrados: verifique.', 'danger')
            return redirect(url_for('inventario'))

        return render_template('inventario_contar.html',
                               inv=inv,
                               itens=itens,
                               alertas_count=get_alertas_count())
    except Exception as e:
        print(f"DEBUG ERRO: {e}")
        import traceback
        traceback.print_exc()
        flash(f'❌ Erro detalhado: {str(e)}', 'danger')
        return redirect(url_for('inventario'))


@app.route('/inventario/<int:inv_id>/salvar_contagem', methods=['POST'])
def salvar_contagem(inv_id):
    try:
        with conectar() as conn:
            itens = conn.execute('''
                SELECT ii.id, ii.estoque_sistema, ii.produto_id
                FROM inventario_itens ii
                WHERE ii.inventario_id = ?
            ''', (inv_id,)).fetchall()

            for item in itens:
                contado = int(request.form.get(f'contado_{item["id"]}', 0) or 0)
                diferenca = contado - item['estoque_sistema']
                conn.execute('''
                    UPDATE inventario_itens 
                    SET estoque_contado = ?, diferenca = ?
                    WHERE id = ?
                ''', (contado, diferenca, item['id']))

        flash('✅ Contagem salva com sucesso!', 'success')
        return redirect(url_for('resultado_inventario', id=inv_id))

    except Exception as e:
        flash(f'❌ Erro: {str(e)}', 'danger')
        return redirect(url_for('contar_inventario', id=inv_id))


@app.route('/inventario/<int:id>/resultado')
def resultado_inventario(id):
    try:
        with conectar() as conn:
            inv = conn.execute('SELECT * FROM inventarios WHERE id = ?', (id,)).fetchone()
            itens = conn.execute('''
                SELECT ii.id, ii.estoque_sistema, ii.estoque_contado, ii.diferenca, ii.ajustado,
                       p.id as produto_id, p.nome as produto, p.codigo, p.localizacao
                FROM inventario_itens ii
                JOIN produtos p ON ii.produto_id = p.id
                WHERE ii.inventario_id = ?
                ORDER BY ii.diferenca ASC
            ''', (id,)).fetchall()

        total_itens = len(itens)
        com_divergencia = sum(1 for i in itens if i['diferenca'] != 0)
        sem_divergencia = total_itens - com_divergencia

        return render_template('inventario_resultado.html',
                               inv=inv,
                               itens=itens,
                               total_itens=total_itens,
                               com_divergencia=com_divergencia,
                               sem_divergencia=sem_divergencia,
                               alertas_count=get_alertas_count())
    except Exception as e:
        flash(f'❌ Erro: {str(e)}', 'danger')
        return redirect(url_for('inventario'))


@app.route('/inventario/<int:inv_id>/ajustar', methods=['POST'])
def ajustar_inventario(inv_id):
    try:
        with conectar() as conn:
            itens = conn.execute('''
                SELECT ii.id, ii.produto_id, ii.estoque_contado, ii.diferenca
                FROM inventario_itens ii
                WHERE ii.inventario_id = ? AND ii.diferenca != 0 AND ii.ajustado = 0
            ''', (inv_id,)).fetchall()

            for item in itens:
                # Atualiza o estoque do produto com o valor contado
                conn.execute('''
                    UPDATE produtos SET estoque_atual = ? WHERE id = ?
                ''', (item['estoque_contado'], item['produto_id']))

                # Marca o item como ajustado
                conn.execute('''
                    UPDATE inventario_itens SET ajustado = 1 WHERE id = ?
                ''', (item['id'],))

            # Fecha o inventário
            conn.execute('''
                UPDATE inventarios SET status = 'FECHADO' WHERE id = ?
            ''', (inv_id,))

        _alertas_cache['timestamp'] = None
        flash('✅ Estoque ajustado e inventário fechado com sucesso!', 'success')
        return redirect(url_for('resultado_inventario', id=inv_id))

    except Exception as e:
        flash(f'❌ Erro: {str(e)}', 'danger')
        return redirect(url_for('resultado_inventario', id=inv_id))

if __name__ == '__main__':
    app.run(debug=True)