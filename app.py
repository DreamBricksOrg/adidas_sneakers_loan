from doctest import debug

from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask
from login_manager import login_manager, auth
from config.database import initialize_mysql
from veiculo import veiculo
from sms_sender import sms_sender
from user import user
from promoter import promoter, aumentar_base
from admin import admin
from datetime import datetime, timedelta
import random

app = Flask(__name__)

# configuration
app.secret_key = 'db_secret'

# init apps
mysql = initialize_mysql(app)
login_manager.init_app(app)

# register blueprints
app.register_blueprint(auth)
app.register_blueprint(veiculo)
app.register_blueprint(user)
app.register_blueprint(sms_sender)
app.register_blueprint(promoter)
app.register_blueprint(admin)


def atualizar_status():
    try:
        # Conectar ao banco de dados
        with app.app_context():
            cur = mysql.connection.cursor()

            # Obter a data atual
            now = datetime.now()
            expiration = now - timedelta(minutes=45)

            # Consulta SQL para atualizar o status
            cur.execute("UPDATE Locacao SET status = 'VENCIDO' WHERE data_inicio < %s AND status = 'ALOCADO' ",
                        (expiration,))

            mysql.connection.commit()

            # Fechar o cursor
            cur.close()

            print('Status atualizado com sucesso.' + now.strftime('%Y-%m-%d %H:%M:%S'))

    except Exception as e:
        print(str(e))


def tarefa_aumentar_base():
    data_desejada = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    quantidade_desejada = random.randint(40, 60)

    resultado = aumentar_base(data_desejada, quantidade_desejada)
    print(f"Tarefa executada: {resultado}")


# Configuração do agendador de tarefas
scheduler = BackgroundScheduler()

# Atualiza o status a cada 5 minutos
scheduler.add_job(atualizar_status, 'interval', minutes=5)

# Executa aumentar_base todos os dias às 3h da manhã
scheduler.add_job(tarefa_aumentar_base, 'cron', hour=3, minute=0)

scheduler.start()

# Para garantir que o scheduler pare corretamente ao desligar o Flask
import atexit
atexit.register(lambda: scheduler.shutdown())

def main():
    context = ('static/certificate.crt', 'static/privateKey.key')
    app.run(host='0.0.0.0', ssl_context=context)

if __name__ == '__main__':
    main()