from flask import Flask, render_template
from flask_socketio import SocketIO
from login_manager import login_manager, auth
from database import initialize_mysql
from local import local
from user import user



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




if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)