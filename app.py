import os
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func, text

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'segredo_super_secreto')

# Configuração do Banco
database_url = os.environ.get('DATABASE_URL')
if database_url and database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = database_url or 'sqlite:///motoboy_local.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# --- MODELOS ---
class User(UserMixin, db.Model):
    __tablename__ = 'usuarios'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    senha = db.Column(db.String(255), nullable=False)
    meta_diaria = db.Column(db.Float, default=200.0)
    transacoes = db.relationship('Transacao', backref='usuario', lazy=True)

class Transacao(db.Model):
    __tablename__ = 'transacoes'
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    tipo = db.Column(db.String(50), nullable=False)
    valor = db.Column(db.Float, nullable=False)
    descricao = db.Column(db.String(200))
    data = db.Column(db.String(10), default=datetime.now().strftime('%Y-%m-%d'))

# --- UTILITÁRIOS ---
@app.template_filter('format_currency')
def format_currency(value):
    try:
        return f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return "0,00"

# --- LOGIN ---
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- ROTAS ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['senha']
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
        
        if User.query.filter_by(email=email).first():
            flash('E-mail já cadastrado.')
            return redirect(url_for('registro'))
        
        senha_hash = generate_password_hash(senha)
        novo_usuario = User(nome=nome, email=email, senha=senha_hash, meta_diaria=200.0)
        
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

@app.route('/')
@login_required
def index():
    user_id = current_user.id
    hoje = datetime.now().strftime('%Y-%m-%d')
    inicio_mes = datetime.now().strftime('%Y-%m-01')
    
    # Valores
    fat_dia = db.session.query(func.sum(Transacao.valor)).filter_by(tipo='entrada', data=hoje, usuario_id=user_id).scalar() or 0
    gasto_dia = db.session.query(func.sum(Transacao.valor)).filter_by(tipo='saida', data=hoje, usuario_id=user_id).scalar() or 0
    fat_mes = db.session.query(func.sum(Transacao.valor)).filter(Transacao.tipo=='entrada', Transacao.data >= inicio_mes, Transacao.usuario_id == user_id).scalar() or 0
    
    # Transações (Últimas 20)
    transacoes = Transacao.query.filter_by(usuario_id=user_id).order_by(Transacao.id.desc()).limit(20).all()
    
    saldo_dia = fat_dia - gasto_dia

    # Meta
    meta = current_user.meta_diaria or 200.0
    porcentagem = int((fat_dia / meta) * 100) if meta > 0 else 0
    largura_barra = 100 if porcentagem > 100 else porcentagem
    
    cor_barra = 'bg-danger'
    if porcentagem >= 50: cor_barra = 'bg-warning'
    if porcentagem >= 100: cor_barra = 'bg-success'
    
    return render_template('index.html', 
                           fat_dia=fat_dia, 
                           gasto_dia=gasto_dia, 
                           saldo_dia=saldo_dia, 
                           fat_mes=fat_mes, 
                           transacoes=transacoes, 
                           nome=current_user.nome,
                           meta=meta,
                           porcentagem=porcentagem,
                           largura_barra=largura_barra,
                           cor_barra=cor_barra)

@app.route('/definir_meta', methods=['POST'])
@login_required
def definir_meta():
    nova_meta = request.form.get('meta')
    if nova_meta:
        current_user.meta_diaria = float(nova_meta)
        db.session.commit()
        flash('Meta atualizada!')
    return redirect(url_for('index'))

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

@app.route('/deletar/<int:id>')
@login_required
def deletar(id):
    transacao = Transacao.query.get_or_404(id)
    if transacao.usuario_id == current_user.id:
        db.session.delete(transacao)
        db.session.commit()
        flash('Item removido!')
    return redirect(url_for('index'))

@app.route('/dados_grafico')
@login_required
def dados_grafico():
    user_id = current_user.id
    # Pega os últimos 7 dias
    dados = []
    
    for i in range(6, -1, -1):
        data_alvo = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
        dia_str = (datetime.now() - timedelta(days=i)).strftime('%d/%m')
        
        entradas = db.session.query(func.sum(Transacao.valor)).filter_by(usuario_id=user_id, data=data_alvo, tipo='entrada').scalar() or 0
        saidas = db.session.query(func.sum(Transacao.valor)).filter_by(usuario_id=user_id, data=data_alvo, tipo='saida').scalar() or 0
        
        dados.append({
            'dia': dia_str,
            'entrada': entradas,
            'saida': saidas
        })
            
    return jsonify(dados)

with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)