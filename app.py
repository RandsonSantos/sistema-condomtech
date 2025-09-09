from datetime import datetime
from functools import wraps
from io import BytesIO
import os

from flask import (
    Flask, flash, render_template, request, redirect,
    url_for, make_response, session
)
from flask_sqlalchemy import SQLAlchemy
from flask_session import Session
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash, check_password_hash
from xhtml2pdf import pisa

# ✅ Importa o db corretamente do models.py
from models import db  # db já foi instanciado lá

# 🚀 Inicializa o app Flask
app = Flask(__name__)

# 🔐 Chave secreta segura
app.secret_key = os.getenv('SECRET_KEY', 'chave_super_secreta_123')

# 🌐 Configuração do banco de dados
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://db_siscondomtech_uyjv_user:rvikfkFZcDGXUj9cOw25X2e3603MW3vu@dpg-d2vo09vdiees738iur7g-a.oregon-postgres.render.com/db_siscondomtech_uyjv'  # ou use os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 🗂️ Configuração de sessão
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = False
Session(app)

# 🔄 Inicializa extensões
db.init_app(app)
migrate = Migrate(app, db)

# ✅ Cria as tabelas se necessário
with app.app_context():
    db.create_all()

# 🧩 Importa modelos
from models import Empresa, Servico, Usuario, Cliente, Produto, OrdemServico, ItemOS

# 🔒 Decorador de login
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'usuario_id' not in session:
            flash("Você precisa estar logado para acessar esta página.", "warning")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# 🏠 Rotas principais
@app.route('/')
@login_required
def index():
    return redirect(url_for('home'))

@app.route('/home')
@login_required
def home():
    return render_template('home.html')

# 🔑 Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        senha = request.form.get('senha')

        usuario = Usuario.query.filter_by(username=username).first()
        if usuario and check_password_hash(usuario.senha, senha):
            session['usuario_id'] = usuario.id
            flash("Login realizado com sucesso!", "success")
            return redirect(url_for('home'))
        else:
            flash("Usuário ou senha inválidos.", "danger")
            return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash("Você saiu da sessão.", "info")
    return redirect(url_for('login'))

# 👤 Cadastro de usuário
@app.route('/cadastrar_usuario', methods=['GET', 'POST'])
@login_required
def cadastrar_usuario():
    if request.method == 'POST':
        username = request.form.get('username')
        senha = request.form.get('senha')
        confirmar = request.form.get('confirmar_senha')

        if not username or not senha:
            flash("Usuário e senha são obrigatórios.", "danger")
            return redirect(url_for('cadastrar_usuario'))
        if senha != confirmar:
            flash("As senhas não coincidem.", "warning")
            return redirect(url_for('cadastrar_usuario'))

        hashed_password = generate_password_hash(senha)
        novo_usuario = Usuario(username=username, senha=hashed_password)
        db.session.add(novo_usuario)
        db.session.commit()
        flash("Usuário cadastrado com sucesso!", "success")
        return redirect(url_for('login'))

    return render_template('cadastrar_usuario.html')

@app.route('/usuarios')
@login_required
def listar_usuarios():
    usuarios = Usuario.query.all()
    return render_template('usuarios.html', usuarios=usuarios)

@app.route('/usuario/editar/<int:usuario_id>', methods=['GET', 'POST'])
@login_required
def editar_usuario(usuario_id):
    usuario = Usuario.query.get_or_404(usuario_id)
    if request.method == 'POST':
        usuario.username = request.form.get('username')
        nova_senha = request.form.get('senha')
        if nova_senha:
            usuario.senha = generate_password_hash(nova_senha)
        db.session.commit()
        flash("Usuário atualizado com sucesso!", "success")
        return redirect(url_for('listar_usuarios'))
    return render_template('editar_usuario.html', usuario=usuario)

@app.route('/usuario/excluir/<int:usuario_id>')
@login_required
def excluir_usuario(usuario_id):
    usuario = Usuario.query.get_or_404(usuario_id)
    db.session.delete(usuario)
    db.session.commit()
    flash("Usuário excluído com sucesso!", "info")
    return redirect(url_for('listar_usuarios'))

# 👤 Cadastro de Cliente
@app.route('/cadastrar_cliente', methods=['GET', 'POST'])
@login_required
def cadastrar_cliente():
    if request.method == 'POST':
        nome = request.form.get('nome')
        telefone = request.form.get('telefone')
        email = request.form.get('email')
        cpf_cnpj = request.form.get('cpf_cnpj')
        cidade = request.form.get('cidade')

        if not nome or not cpf_cnpj:
            flash("Nome e CPF/CNPJ são obrigatórios.", "danger")
            return redirect(url_for('cadastrar_cliente'))

        novo_cliente = Cliente(
            nome=nome,
            telefone=telefone,
            email=email,
            cpf_cnpj=cpf_cnpj,
            cidade=cidade
        )
        db.session.add(novo_cliente)
        db.session.commit()
        flash("Cliente cadastrado com sucesso!", "success")
        return redirect(url_for('listar_clientes'))

    return render_template('cadastrar_cliente.html')

@app.route('/cliente/<int:cliente_id>/editar', methods=['GET', 'POST'])
@login_required
def editar_cliente(cliente_id):
    cliente = Cliente.query.get_or_404(cliente_id)

    if request.method == 'POST':
        cliente.nome = request.form.get('nome')
        cliente.telefone = request.form.get('telefone')
        cliente.email = request.form.get('email')
        cliente.cpf_cnpj = request.form.get('cpf_cnpj')

        db.session.commit()
        flash("Cliente atualizado com sucesso!", "success")
        return redirect(url_for('listar_clientes'))

    return render_template('editar_cliente.html', cliente=cliente)

@app.route('/clientes')
@login_required
def listar_clientes():
    termo = request.args.get('busca', '').strip()
    if termo:
        clientes = Cliente.query.filter(
            db.or_(
                Cliente.nome.ilike(f'%{termo}%'),
                Cliente.cpf_cnpj.ilike(f'%{termo}%'),
                Cliente.email.ilike(f'%{termo}%')
            )
        ).order_by(Cliente.nome).all()
    else:
        clientes = Cliente.query.order_by(Cliente.nome).all()
    return render_template('clientes.html', clientes=clientes)

# 🔍 Ordens por cliente
@app.route('/cliente/<int:cliente_id>/ordens')
@login_required
def ordens_por_cliente(cliente_id):
    cliente = Cliente.query.get_or_404(cliente_id)
    ordens = OrdemServico.query.filter_by(cliente_id=cliente.id).order_by(OrdemServico.data_criacao.desc()).all()

    lista_os = []
    for os in ordens:
        total = sum(item.quantidade * item.produto.preco for item in os.itens_os if item.produto)
        lista_os.append({'os': os, 'total': total})

    return render_template('ordens_por_cliente.html', cliente=cliente, lista_os=lista_os)

# ✏️ Editar Ordem de Serviço
@app.route('/os/<int:os_id>/editar', methods=['GET', 'POST'])
@login_required
def editar_os(os_id):
    os = OrdemServico.query.get_or_404(os_id)
    produtos = Produto.query.all()

    if request.method == 'POST':
        try:
            os.data_criacao = datetime.strptime(request.form.get('data_criacao'), '%Y-%m-%d')
        except (ValueError, TypeError):
            flash("Data inválida.", "danger")
            return redirect(url_for('editar_os', os_id=os.id))

        os.status = request.form.get('status')
        os.desconto = float(request.form.get('desconto') or 0)

        # Remover item
        excluir_id = request.form.get('excluir_item')
        if excluir_id:
            item = ItemOS.query.get(int(excluir_id))
            if item and item.os_id == os.id:
                db.session.delete(item)
                db.session.commit()
                flash("Item removido com sucesso.", "info")
                return redirect(url_for('editar_os', os_id=os.id))

        # Atualizar quantidade
        for item in os.itens_os:
            qtd = request.form.get(f'quantidade_{item.id}')
            if qtd:
                item.quantidade = int(qtd)

        # Adicionar novo item
        if request.form.get('adicionar_item'):
            produto_id = request.form.get('novo_produto_id')
            quantidade = request.form.get('nova_quantidade')
            if produto_id and quantidade:
                produto = Produto.query.get(int(produto_id))
                if produto:
                    novo_item = ItemOS(
                        os_id=os.id,
                        produto_id=produto.id,
                        quantidade=int(quantidade)
                    )
                    db.session.add(novo_item)

        db.session.commit()
        flash("Ordem de serviço atualizada com sucesso!", "success")
        return redirect(url_for('ordens_por_cliente', cliente_id=os.cliente_id))

    return render_template('editar_os.html', os=os, produtos=produtos)

# ➕ Nova OS para cliente específico
@app.route('/nova_os/cliente/<int:cliente_id>', methods=['GET', 'POST'])
@login_required
def nova_os_para_cliente(cliente_id):
    cliente = Cliente.query.get_or_404(cliente_id)
    produtos = Produto.query.all()

    if request.method == 'POST':
        observacoes = request.form.get('observacoes')
        nova_os = OrdemServico(cliente_id=cliente.id, observacoes=observacoes)
        db.session.add(nova_os)
        db.session.commit()

        produtos_ids = request.form.getlist('produto')
        quantidades = request.form.getlist('quantidade')

        for pid, qtd in zip(produtos_ids, quantidades):
            if pid and qtd:
                item = ItemOS(
                    os_id=nova_os.id,
                    produto_id=int(pid),
                    quantidade=int(qtd)
                )
                db.session.add(item)

        db.session.commit()
        flash("Ordem de serviço criada com sucesso!", "success")
        return redirect(url_for('visualizar_os', os_id=nova_os.id))

    return render_template('nova_os.html', cliente=cliente, produtos=produtos)

# 📦 Listar produtos
@app.route('/produtos')
@login_required
def listar_produtos():
    nome = request.args.get('nome', '').strip()
    tipo = request.args.get('tipo', '').strip()

    query = Produto.query
    if nome:
        query = query.filter(Produto.nome.ilike(f'%{nome}%'))
    if tipo:
        query = query.filter(Produto.tipo == tipo)

    produtos = query.order_by(Produto.nome.asc()).all()
    return render_template('produtos.html', produtos=produtos, nome=nome, tipo=tipo)

# 🛒 Cadastrar produto
@app.route('/cadastrar_produto', methods=['GET', 'POST'])
@login_required
def cadastrar_produto():
    if request.method == 'POST':
        nome = request.form.get('nome')
        descricao = request.form.get('descricao')
        preco = request.form.get('preco')
        tipo = request.form.get('tipo')

        if not nome or not preco or not tipo:
            flash("Nome, preço e tipo são obrigatórios.", "danger")
            return redirect(url_for('cadastrar_produto'))

        try:
            preco_float = float(preco)
        except ValueError:
            flash("Preço inválido.", "danger")
            return redirect(url_for('cadastrar_produto'))

        novo_produto = Produto(nome=nome, descricao=descricao, preco=preco_float, tipo=tipo)
        db.session.add(novo_produto)
        db.session.commit()
        flash("Produto cadastrado com sucesso!", "success")
        return redirect(url_for('listar_produtos'))

    return render_template('cadastrar_produto.html')

# ✏️ Editar produto
@app.route('/produto/<int:produto_id>/editar', methods=['GET', 'POST'])
@login_required
def editar_produto(produto_id):
    produto = Produto.query.get_or_404(produto_id)

    if request.method == 'POST':
        nome = request.form.get('nome')
        descricao = request.form.get('descricao')
        preco = request.form.get('preco')

        if not nome or not preco:
            flash("Nome e preço são obrigatórios.", "danger")
            return redirect(url_for('editar_produto', produto_id=produto.id))

        try:
            produto.preco = float(preco)
        except ValueError:
            flash("Preço inválido.", "danger")
            return redirect(url_for('editar_produto', produto_id=produto.id))

        produto.nome = nome
        produto.descricao = descricao

        db.session.commit()
        flash("Produto atualizado com sucesso!", "success")
        return redirect(url_for('listar_produtos'))

    return render_template('editar_produto.html', produto=produto)

# ➕ Nova OS geral
@app.route('/nova_os', methods=['GET', 'POST'])
@login_required
def nova_os():
    clientes = Cliente.query.order_by(Cliente.nome).all()
    produtos = Produto.query.order_by(Produto.nome).all()

    if request.method == 'POST':
        cliente_id = request.form.get('cliente')
        produto_ids = request.form.getlist('produto[]')
        quantidades = request.form.getlist('quantidade[]')
        desconto = float(request.form.get('desconto') or 0)
        observacoes = request.form.get('observacoes')

        if not cliente_id or not produto_ids or not quantidades:
            flash("Preencha todos os campos obrigatórios.", "danger")
            return redirect(url_for('nova_os'))

        os = OrdemServico(
            cliente_id=cliente_id,
            desconto=desconto,
            observacoes=observacoes,
            status='Aberta'
        )
        db.session.add(os)
        db.session.flush()  # Garante que os.id esteja disponível

        for pid, qtd in zip(produto_ids, quantidades):
            if pid and qtd:
                item = ItemOS(
                    os_id=os.id,
                    produto_id=int(pid),
                    quantidade=int(qtd)
                )
                db.session.add(item)

        db.session.commit()
        flash("Ordem de Serviço criada com sucesso!", "success")
        return redirect(url_for('visualizar_os', os_id=os.id))

    cliente_id = request.args.get('cliente_id')
    cliente = Cliente.query.get(cliente_id) if cliente_id else None

    return render_template('nova_os.html', clientes=clientes, produtos=produtos, cliente=cliente)

# 👁️ Visualizar OS
@app.route('/os/<int:os_id>')
@login_required
def visualizar_os(os_id):
    os = OrdemServico.query.get_or_404(os_id)
    subtotal = sum(item.quantidade * item.produto.preco for item in os.itens_os if item.produto)
    total = max(subtotal - (os.desconto or 0), 0)
    return render_template('visualizar_os.html', os=os, subtotal=subtotal, total=total)

# 🖨️ Gerar PDF da Ordem de Serviço
@app.route('/os/<int:os_id>/pdf')
@login_required
def gerar_pdf(os_id):
    try:
        os = OrdemServico.query.get_or_404(os_id)
        empresa = Empresa.query.first()

        subtotal = sum(item.quantidade * item.produto.preco for item in os.itens_os if item.produto)
        total = max(subtotal - (os.desconto or 0), 0)

        html = render_template('os_pdf.html', os=os, subtotal=subtotal, total=total, empresa=empresa)

        result = BytesIO()
        pisa_status = pisa.CreatePDF(html, dest=result)

        if pisa_status.err:
            flash("Erro ao gerar PDF.", "danger")
            return redirect(url_for('visualizar_os', os_id=os.id))

        response = make_response(result.getvalue())
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'inline; filename=os_{os.id}.pdf'
        return response

    except Exception as e:
        flash(f"Erro inesperado: {str(e)}", "danger")
        return redirect(url_for('visualizar_os', os_id=os_id))

# 💰 Filtro de moeda
@app.template_filter('moeda')
def moeda(valor):
    try:
        return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except (TypeError, ValueError):
        return "R$ 0,00"

# 🕒 Contexto global com datetime
@app.context_processor
def inject_datetime():
    return {'datetime': datetime}

# 🏢 Dados da empresa
@app.route('/empresa', methods=['GET', 'POST'])
@login_required
def empresa():
    empresa = Empresa.query.first()

    if request.method == 'POST':
        if not empresa:
            empresa = Empresa()
            db.session.add(empresa)

        empresa.nome = request.form.get('nome')
        empresa.endereco = request.form.get('endereco')
        empresa.telefone = request.form.get('telefone')
        empresa.email = request.form.get('email')
        empresa.cnpj = request.form.get('cnpj')
        empresa.observacoes = request.form.get('observacoes')
        empresa.site = request.form.get('site')

        db.session.commit()
        flash("Dados da empresa atualizados com sucesso!", "success")
        return redirect(url_for('empresa'))

    return render_template('empresa.html', empresa=empresa)

@app.route('/empresa/editar', methods=['GET', 'POST'])
@login_required
def editar_empresa():
    empresa = Empresa.query.first()

    if request.method == 'POST':
        if not empresa:
            empresa = Empresa()
            db.session.add(empresa)

        empresa.nome = request.form.get('nome')
        empresa.endereco = request.form.get('endereco')
        empresa.telefone = request.form.get('telefone')
        empresa.email = request.form.get('email')
        empresa.cnpj = request.form.get('cnpj')
        empresa.site = request.form.get('site')
        empresa.observacoes = request.form.get('observacoes')

        db.session.commit()
        flash("Empresa atualizada com sucesso!", "success")
        return redirect(url_for('empresa'))

    return render_template('editar_empresa.html', empresa=empresa)

# 📊 Dashboard
@app.route('/dashboard')
@login_required
def dashboard():
    total_os = OrdemServico.query.count()
    total_clientes = Cliente.query.count()

    valor_total = sum(os.total for os in OrdemServico.query.all())
    valor_pago = sum(os.total for os in OrdemServico.query.filter_by(status='Pago').all())
    valor_cancelado = sum(os.total for os in OrdemServico.query.filter_by(status='Cancelado').all())
    valor_aberto = sum(os.total for os in OrdemServico.query.filter_by(status='Aberta').all())

    hoje = datetime.today()
    inicio_mes = datetime(hoje.year, hoje.month, 1)
    ultimas_ordens = (
        OrdemServico.query
        .filter(OrdemServico.data_criacao >= inicio_mes)
        .order_by(OrdemServico.data_criacao.desc())
        .limit(4)  # ✅ agora pega só os 4 últimos
        .all()
    )

    return render_template(
        'dashboard.html',
        total_os=total_os,
        total_clientes=total_clientes,
        valor_total=valor_total,
        valor_pago=valor_pago,
        valor_cancelado=valor_cancelado,
        valor_aberto=valor_aberto,
        ultimas_ordens=ultimas_ordens
    )

# 🔎 Busca de ordens
@app.route('/ordens')
@login_required
def buscar_ordens():
    termo = request.args.get('busca', '').strip()
    status = request.args.get('status', '').strip()
    mes = request.args.get('mes', '').strip()
    page = request.args.get('page', 1, type=int)

    query = OrdemServico.query.join(Cliente)
    filtros = []

    if termo:
        filtros.append(
            db.or_(
                Cliente.nome.ilike(f'%{termo}%'),
                db.cast(OrdemServico.data_criacao, db.String).ilike(f'%{termo}%')
            )
        )
    if status:
        filtros.append(OrdemServico.status == status)
    if mes.isdigit() and 1 <= int(mes) <= 12:
        filtros.append(db.extract('month', OrdemServico.data_criacao) == int(mes))

    if filtros:
        query = query.filter(*filtros)

    paginadas = query.order_by(OrdemServico.data_criacao.desc()).paginate(page=page, per_page=10)

    return render_template('buscar_ordens.html', ordens=paginadas.items, termo=termo, status=status, mes=mes, paginadas=paginadas)

# 📋 Listar ordens por status
@app.route('/ordens/<status>')
@login_required
def listar_ordens_por_status(status):
    status_permitidos = ['Aberta', 'Em andamento', 'Finalizada', 'Cancelada', 'Pago']
    
    status_formatado = status.capitalize()
    if status_formatado not in status_permitidos:
        flash('Status inválido.', 'warning')
        return redirect(url_for('dashboard'))

    ordens = OrdemServico.query.filter(OrdemServico.status.ilike(status_formatado))\
        .order_by(OrdemServico.data_criacao.desc()).all()

    return render_template('lista_ordens.html', ordens=ordens, status=status_formatado)

# 🚀 Executa o servidor localmente
if __name__ == '__main__':
    app.run(debug=True)


