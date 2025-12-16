from app import app, db

# Força a criação das tabelas agora
with app.app_context():
    try:
        db.create_all()
        print("✅ SUCESSO! Banco de dados 'motoboy_local.db' criado com as novas tabelas!")
        print("Agora pode rodar o 'python app.py'")
    except Exception as e:
        print(f"❌ ERRO: {e}")