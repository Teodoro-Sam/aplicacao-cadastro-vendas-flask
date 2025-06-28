# database.py
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Cliente(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome_completo = db.Column(db.String(100), nullable=False)
    cpf = db.Column(db.String(14), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    data_nascimento = db.Column(db.String(10), nullable=False) # Formato YYYY-MM-DD

    def __repr__(self):
        return f"<Cliente {self.nome_completo}>"

class Produto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    marca = db.Column(db.String(50), nullable=False)
    peso = db.Column(db.Float, nullable=False)
    quantidade = db.Column(db.Integer, nullable=False)
    valor = db.Column(db.Float, nullable=False)

    def __repr__(self):
        return f"<Produto {self.nome}>"

class VendaItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    venda_id = db.Column(db.Integer, db.ForeignKey('venda.id'), nullable=False)
    produto_id = db.Column(db.Integer, db.ForeignKey('produto.id'), nullable=False)
    quantidade = db.Column(db.Integer, nullable=False)
    preco_unitario = db.Column(db.Float, nullable=False)
    
    produto = db.relationship('Produto', backref='itens_venda')

    def __repr__(self):
        return f"<VendaItem Venda:{self.venda_id} Produto:{self.produto_id}>"

class Venda(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    data_venda = db.Column(db.DateTime, nullable=False, default=db.func.now())
    valor_total = db.Column(db.Float, nullable=False)
    itens = db.relationship('VendaItem', backref='venda', lazy=True)

    def __repr__(self):
        return f"<Venda {self.id}>"