from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user
from flask import render_template, redirect, url_for, request, Blueprint
from database import mysql

login_manager = LoginManager()
auth = Blueprint('auth', __name__)


class User(UserMixin):
    def __init__(self, user_id):
        self.id = user_id

@login_manager.user_loader
def load_user(user_id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM UsuarioAdmin WHERE id = %s", (user_id,))
    user_data = cur.fetchone()
    cur.close()
    if not user_data:
        return None
    return User(user_id)

@login_manager.unauthorized_handler
def unauthorized():
    return render_template('acesso_negado.html')

@auth.route('/register', methods=['GET', 'POST'])
@login_required
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM UsuarioAdmin WHERE username = %s", (username,))
        if cur.fetchone():
            cur.close()
            return 'Nome de usuário já existe. Escolha outro nome de usuário.'
        cur.execute("INSERT INTO  (username, password) VALUES (%s, %s)", (username, password))
        mysql.connection.commit()
        cur.close()
        return 'Cadastro realizado com sucesso. <a href="/">Ir para a página inicial</a>'
    return render_template('register.html')

@auth.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM UsuarioAdmin WHERE username = %s", (username,))
        user_data = cur.fetchone()
        cur.close()
        if user_data and user_data[2] == password:
            user = User(user_data[0])
            login_user(user)
            if request.form['submit_button'] == 'Entrar':
                return redirect(url_for('index'))
        return render_template('acesso_negado.html')
    return render_template('login.html')

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))
