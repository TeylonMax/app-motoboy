import os
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'segredo_super_secreto')

# --- CONFIGURAÇÃO DO BANCO DE DADOS (RENDER + LOCAL) ---
database_url = os.environ.get('DATABASE_URL')

# Correção necessária para o Render (postgres:// -> postgresql://)
if database_url and database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

# Se não tiver URL do Render, usa um SQLite local chamado 'motoboy_local.db'
app.config['SQLALCHEMY_DATABASE_URI'] = database_url or 'sqlite:///motoboy_local.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# --- MODELOS (TABELAS DO BANCO) ---

class User(UserMixin, db.Model):
    __tablename__ = 'usuarios'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    senha = db.Column(db.String(255), nullable=False)
    # Relacionamento com transações
    transacoes = db.relationship('Transacao', backref='usuario', lazy=True)

class Transacao(db.Model):
    __tablename__ = 'transacoes'
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    tipo = db.Column(db.String(50), nullable=False) # 'entrada' ou 'saida'
    valor = db.Column(db.Float, nullable=False)
    descricao = db.Column(db.String(200))
    data = db.Column(db.String(10), default=datetime.now().strftime('%Y-%m-%d'))

# --- CONFIGURAÇÃO DO LOGIN ---
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- ROTAS DE AUTENTICAÇÃO ---

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['senha']
        
        # Busca usuário no banco pelo e-mail
        user = User.query.filter_by(email=email).first()
        
        if user and check_password_hash(user.senha, senha):
            login_user(user)
            return redirect(url_for('index'))
        else:
            flash('Login inválido. Verifique e-mail e senha.')
            
    return render_template('login.html')

@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']
        senha = request.form['senha']
        
        # Verifica se já existe
        if User.query.filter_by(email=email).first():
            flash('E-mail já cadastrado.')
            return redirect(url_for('registro'))
        
        senha_hash = generate_password_hash(senha)
        novo_usuario = User(nome=nome, email=email, senha=senha_hash)
        
        try:
            db.session.add(novo_usuario)
            db.session.commit()
            flash('Conta criada! Faça login.')
            return redirect(url_for('login'))
        except:
            flash('Erro ao criar conta.')
            
    return render_template('registro.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# --- ROTAS DA APLICAÇÃO (PROTEGIDAS) ---

@app.route('/')
@login_required
def index():
    user_id = current_user.id
    hoje = datetime.now().strftime('%Y-%m-%d')
    inicio_mes = datetime.now().strftime('%Y-%m-01')
    
    # Consultas usando SQLAlchemy (Soma de valores)
    fat_dia = db.session.query(func.sum(Transacao.valor)).filter_by(tipo='entrada', data=hoje, usuario_id=user_id).scalar() or 0
    gasto_dia = db.session.query(func.sum(Transacao.valor)).filter_by(tipo='saida', data=hoje, usuario_id=user_id).scalar() or 0
    fat_mes = db.session.query(func.sum(Transacao.valor)).filter(Transacao.tipo=='entrada', Transacao.data >= inicio_mes, Transacao.usuario_id == user_id).scalar() or 0
    
    # Lista das últimas 10 transações
    transacoes = Transacao.query.filter_by(usuario_id=user_id).order_by(Transacao.id.desc()).limit(10).all()
    
    saldo_dia = fat_dia - gasto_dia
    
    return render_template('index.html', fat_dia=fat_dia, gasto_dia=gasto_dia, saldo_dia=saldo_dia, fat_mes=fat_mes, transacoes=transacoes, nome=current_user.nome)

@app.route('/adicionar', methods=('POST',))
@login_required
def adicionar():
    if request.method == 'POST':
        tipo = request.form['tipo']
        valor = float(request.form['valor'])
        descricao = request.form['descricao']
        
        nova_transacao = Transacao(
            usuario_id=current_user.id,
            tipo=tipo,
            valor=valor,
            descricao=descricao,
            data=datetime.now().strftime('%Y-%m-%d')
        )
        
        db.session.add(nova_transacao)
        db.session.commit()
        
    return redirect(url_for('index'))

@app.route('/dados_grafico')
@login_required
def dados_grafico():
    user_id = current_user.id
    data_limite = (datetime.now() - timedelta(days=6)).strftime('%Y-%m-%d')
    
    # Query agrupada
    resultados = db.session.query(
        Transacao.data, Transacao.tipo, func.sum(Transacao.valor)
    ).filter(
        Transacao.data >= data_limite, Transacao.usuario_id == user_id
    ).group_by(Transacao.data, Transacao.tipo).all()
    
    dados = {}
    # Prepara a estrutura dos ultimos 7 dias zerada
    for i in range(7):
        chave_data = (datetime.now() - timedelta(days=6-i)).strftime('%Y-%m-%d')
        dia_formatado = (datetime.now() - timedelta(days=6-i)).strftime('%d/%m')
        dados[chave_data] = {'dia': dia_formatado, 'entrada': 0, 'saida': 0}
        
    # Preenche com os dados do banco
    for data, tipo, total in resultados:
        if data in dados:
            dados[data][tipo] = total
            
    return jsonify({
        'labels': [v['dia'] for v in dados.values()],
        'entradas': [v['entrada'] for v in dados.values()],
        'saidas': [v['saida'] for v in dados.values()]
    })

# Criação das tabelas
# No Render, isso roda automaticamente na primeira vez que alguém acessa, 
# mas o ideal é rodar localmente uma vez para testar.
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)