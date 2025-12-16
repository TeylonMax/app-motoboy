import os
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func, text  # Importe 'text' aqui

app = Flask(__name__)
# Configuração da chave secreta (importante para segurança)
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
    # Nova coluna para a Meta Diária (Padrão R$ 200,00)
    meta_diaria = db.Column(db.Float, default=200.0)
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

# --- ROTA ESPECIAL PARA ATUALIZAR O BANCO (Use uma vez e apague depois se quiser) ---
@app.route('/atualizar_banco_meta')
def atualizar_banco_meta():
    try:
        # Comando SQL para criar a coluna na força bruta caso ela não exista
        with db.engine.connect() as conn:
            conn.execute(text("ALTER TABLE usuarios ADD COLUMN meta_diaria FLOAT DEFAULT 200.0;"))
            conn.commit()
        return "Sucesso! Coluna 'meta_diaria' criada. Agora volte para o app."
    except Exception as e:
        return f"Aviso (provavelmente a coluna já existe): {str(e)}"

# --- ROTAS DE AUTENTICAÇÃO ---

@app.route('/login', methods=['GET', 'POST'])
def login():
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

# --- ROTAS DA APLICAÇÃO (PROTEGIDAS) ---

@app.route('/')
@login_required
def index():
    user_id = current_user.id
    hoje = datetime.now().strftime('%Y-%m-%d')
    inicio_mes = datetime.now().strftime('%Y-%m-01')
    
    # Consultas de valores
    fat_dia = db.session.query(func.sum(Transacao.valor)).filter_by(tipo='entrada', data=hoje, usuario_id=user_id).scalar() or 0
    gasto_dia = db.session.query(func.sum(Transacao.valor)).filter_by(tipo='saida', data=hoje, usuario_id=user_id).scalar() or 0
    fat_mes = db.session.query(func.sum(Transacao.valor)).filter(Transacao.tipo=='entrada', Transacao.data >= inicio_mes, Transacao.usuario_id == user_id).scalar() or 0
    
    # Lista das últimas 10 transações
    transacoes = Transacao.query.filter_by(usuario_id=user_id).order_by(Transacao.id.desc()).limit(10).all()
    
    saldo_dia = fat_dia - gasto_dia

    # --- LÓGICA DA META DIÁRIA ---
    meta = current_user.meta_diaria or 200.0
    porcentagem = int((fat_dia / meta) * 100) if meta > 0 else 0
    
    # Ajustes visuais da barra
    largura_barra = 100 if porcentagem > 100 else porcentagem
    
    cor_barra = 'bg-danger' # Vermelho
    if porcentagem >= 50: cor_barra = 'bg-warning' # Amarelo
    if porcentagem >= 100: cor_barra = 'bg-success' # Verde
    
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

@app.route('/dados_grafico')
@login_required
def dados_grafico():
    user_id = current_user.id
    data_limite = (datetime.now() - timedelta(days=6)).strftime('%Y-%m-%d')
    
    resultados = db.session.query(
        Transacao.data, Transacao.tipo, func.sum(Transacao.valor)
    ).filter(
        Transacao.data >= data_limite, Transacao.usuario_id == user_id
    ).group_by(Transacao.data, Transacao.tipo).all()
    
    dados = {}
    for i in range(7):
        chave_data = (datetime.now() - timedelta(days=6-i)).strftime('%Y-%m-%d')
        dia_formatado = (datetime.now() - timedelta(days=6-i)).strftime('%d/%m')
        dados[chave_data] = {'dia': dia_formatado, 'entrada': 0, 'saida': 0}
        
    for data, tipo, total in resultados:
        if data in dados:
            dados[data][tipo] = total
            
    return jsonify({
        'labels': [v['dia'] for v in dados.values()],
        'entradas': [v['entrada'] for v in dados.values()],
        'saidas': [v['saida'] for v in dados.values()]
    })

# Criação das tabelas localmente
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)