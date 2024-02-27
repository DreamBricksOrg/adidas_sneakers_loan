from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask
from login_manager import login_manager, auth
from config.database import initialize_mysql
from local import local
from sms_sender import sms_sender
from user import user
from promoter import promoter
from datetime import datetime

app = Flask(__name__)

# configuration
app.secret_key = 'db_secret'

# init apps
mysql = initialize_mysql(app)
# socketio = SocketIO(app)
login_manager.init_app(app)

# register blueprints
app.register_blueprint(auth)
app.register_blueprint(local)
app.register_blueprint(user)
app.register_blueprint(sms_sender)
app.register_blueprint(promoter)


def update_status():
    try:

        with app.app_context():
            cur = mysql.connection.cursor()

            now = datetime.now()

            cur.execute("UPDATE Locacao SET status = 'VENCIDO' WHERE data_fim < %s AND status != 'DEVOLVIDO' ", (now,))

            mysql.connection.commit()

            cur.close()

            print('Status atualizado com sucesso.' + now.strftime('%Y-%m-%d %H:%M:%S'))

    except Exception as e:
        print(str(e))


scheduler = BackgroundScheduler()
scheduler.add_job(update_status, 'interval', minutes=5)
scheduler.start()

if __name__ == '__main__':
    context = ('static/certificate.crt', 'static/privateKey.key')
    app.run(host='0.0.0.0', port=5000, ssl_context=context)
