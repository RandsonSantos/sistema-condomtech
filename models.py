from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

# seus modelos aqui...

class Cliente(db.Model):
    __tablename__ = 'clientes'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    telefone = db.Column(db.String(20))
    email = db.Column(db.String(100))
    cpf_cnpj = db.Column(db.String(20), unique=True, nullable=False)
    cidade = db.Column(db.String(100))

    ordens = db.relationship('OrdemServico', backref='cliente', cascade='all, delete-orphan')

    def __repr__(self):
        return f"<Cliente {self.id} - {self.nome}>"


class Produto(db.Model):
    __tablename__ = 'produtos'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    descricao = db.Column(db.String(200))
    preco = db.Column(db.Float, nullable=False)
    tipo = db.Column(db.String(20), nullable=False)  # Produto ou Serviço

    itens_os = db.relationship('ItemOS', backref='produto', cascade='all, delete-orphan')

    def __repr__(self):
        return f"<Produto {self.id} - {self.nome} ({self.tipo})>"


class Servico(db.Model):
    __tablename__ = 'servicos'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    descricao = db.Column(db.String(200))
    preco = db.Column(db.Float, nullable=False)

    def __repr__(self):
        return f"<Servico {self.id} - {self.nome}>"


class OrdemServico(db.Model):
    __tablename__ = 'ordens_servico'
    id = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey('clientes.id'), nullable=False)
    observacoes = db.Column(db.Text)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    desconto = db.Column(db.Float, default=0.0)
    status = db.Column(db.String(50), default='Aberta')

    itens_os = db.relationship('ItemOS', backref='ordem', cascade='all, delete-orphan')

    @property
    def total(self):
        return sum(
            item.quantidade * item.produto.preco
            for item in self.itens_os
            if item.produto
        ) - (self.desconto or 0)

    def __repr__(self):
        return f"<OS {self.id} - Cliente {self.cliente_id}>"


class ItemOS(db.Model):
    __tablename__ = 'itens_os'
    id = db.Column(db.Integer, primary_key=True)
    os_id = db.Column(db.Integer, db.ForeignKey('ordens_servico.id'), nullable=False)
    produto_id = db.Column(db.Integer, db.ForeignKey('produtos.id'), nullable=False)
    quantidade = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return f"<ItemOS {self.id} - OS {self.os_id} - Produto {self.produto_id}>"


class Usuario(db.Model):
    __tablename__ = 'usuarios'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    senha = db.Column(db.String(512), nullable=False)  # <-- ajustado

    def __repr__(self):
        return f"<Usuario {self.id} - {self.username}>"


class Empresa(db.Model):
    __tablename__ = 'empresa'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    endereco = db.Column(db.String(200))
    telefone = db.Column(db.String(20))
    email = db.Column(db.String(100))
    cnpj = db.Column(db.String(20), unique=True)
    observacoes = db.Column(db.Text)
    site = db.Column(db.String(100))

    def __repr__(self):
        return f"<Empresa {self.id} - {self.nome}>"
