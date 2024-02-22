from flask import Flask
from login_manager import login_manager, auth
from database import initialize_mysql
from local import local
from sms_sender import sms_sender
from user import user
from promoter import promoter

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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
