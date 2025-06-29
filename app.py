# app.py
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from database import db, Cliente, Produto, Venda, VendaItem
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///minha_aplicacao.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'sua_chave_secreta_aqui' # Mude isso para uma chave mais forte

# Inicializa o banco de dados
db.init_app(app)

# Cria as tabelas do banco de dados se elas não existirem
with app.app_context():
    db.create_all()

# --- Rotas ---

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/cadastro_cliente', methods=['GET', 'POST'])
def cadastro_cliente():
    if request.method == 'POST':
        nome_completo = request.form['nome_completo']
        cpf = request.form['cpf']
        email = request.form['email']
        data_nascimento = request.form['data_nascimento']

        try:
            novo_cliente = Cliente(
                nome_completo=nome_completo,
                cpf=cpf,
                email=email,
                data_nascimento=data_nascimento
            )
            db.session.add(novo_cliente)
            db.session.commit()
            flash('Cliente cadastrado com sucesso!', 'success')
            return redirect(url_for('cadastro_cliente'))
        except Exception as e:
            flash(f'Erro ao cadastrar cliente: {str(e)}', 'danger')
            db.session.rollback()

    return render_template('cadastro_cliente.html')

@app.route('/cadastro_produto', methods=['GET', 'POST'])
def cadastro_produto():
    if request.method == 'POST':
        nome = request.form['nome']
        marca = request.form['marca']
        peso = float(request.form['peso'])
        quantidade = int(request.form['quantidade'])
        valor = float(request.form['valor'])

        try:
            novo_produto = Produto(
                nome=nome,
                marca=marca,
                peso=peso,
                quantidade=quantidade,
                valor=valor
            )
            db.session.add(novo_produto)
            db.session.commit()
            flash('Produto cadastrado com sucesso!', 'success')
            return redirect(url_for('cadastro_produto'))
        except Exception as e:
            flash(f'Erro ao cadastrar produto: {str(e)}', 'danger')
            db.session.rollback()

    return render_template('cadastro_produto.html')

@app.route('/venda')
def venda_page():
    return render_template('venda.html')

@app.route('/api/produtos')
def api_produtos():
    query = request.args.get('q', '').strip()
    if query:
        produtos = Produto.query.filter(
            (Produto.nome.ilike(f'%{query}%')) |
            (Produto.marca.ilike(f'%{query}%'))
        ).limit(10).all()
    else:
        produtos = []
    
    produtos_data = [{
        'id': p.id,
        'nome': p.nome,
        'marca': p.marca,
        'valor': p.valor,
        'quantidade_estoque': p.quantidade
    } for p in produtos]
    return jsonify(produtos_data)

@app.route('/finalizar_venda', methods=['POST'])
def finalizar_venda():
    dados_venda = request.json
    itens_vendidos = dados_venda.get('itens', [])
    valor_total_venda = 0.0

    try:
        nova_venda = Venda(valor_total=0.0) # Valor_total será atualizado depois
        db.session.add(nova_venda)
        db.session.flush() # Para obter o ID da venda antes de commitar

        for item_data in itens_vendidos:
            produto_id = item_data['produto_id']
            quantidade_vendida = item_data['quantidade']

            produto = Produto.query.get(produto_id)
            if not produto or produto.quantidade < quantidade_vendida:
                raise ValueError(f"Estoque insuficiente para {produto.nome} ou produto não encontrado.")
            
            # Atualiza o estoque do produto
            produto.quantidade -= quantidade_vendida
            
            preco_unitario = produto.valor
            valor_item = preco_unitario * quantidade_vendida
            valor_total_venda += valor_item

            novo_item_venda = VendaItem(
                venda_id=nova_venda.id,
                produto_id=produto_id,
                quantidade=quantidade_vendida,
                preco_unitario=preco_unitario
            )
            db.session.add(novo_item_venda)
        
        nova_venda.valor_total = valor_total_venda
        db.session.commit()
        flash(f'Venda ID {nova_venda.id} finalizada com sucesso! Valor Total: R$ {nova_venda.valor_total:.2f}', 'success')
        return jsonify({'success': True, 'venda_id': nova_venda.id, 'valor_total': nova_venda.valor_total})

    except ValueError as ve:
        db.session.rollback()
        flash(f'Erro na venda: {str(ve)}', 'danger')
        return jsonify({'success': False, 'message': str(ve)}), 400
    except Exception as e:
        db.session.rollback()
        flash(f'Erro inesperado ao finalizar venda: {str(e)}', 'danger')
        return jsonify({'success': False, 'message': f'Erro inesperado: {str(e)}'}), 500

@app.route('/detalhes_venda/<int:venda_id>')
def detalhes_venda(venda_id):
    venda = Venda.query.get_or_404(venda_id)
    return render_template('detalhes_venda.html', venda=venda)

# Nova rota para consulta de estoque
@app.route('/estoque')
def estoque():
    # Consulta todos os produtos ordenados pelo nome
    produtos = Produto.query.order_by(Produto.nome).all()
    return render_template('estoque.html', produtos=produtos)


if __name__ == '__main__':
    app.run(debug=True)