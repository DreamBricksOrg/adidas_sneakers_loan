from flask import Blueprint, request, jsonify, render_template, redirect, url_for
from database import mysql

user = Blueprint('user', __name__)

@user.route('/users', methods=['GET'])
def get_user():
    cursor = mysql.connection.cursor()
    cursor.execute('SELECT * FROM Usuario')
    result = cursor.fetchall()
    cursor.close()
    return jsonify(result), 200

@user.route('/users/<int:id>', methods=['GET'])
def get_user_id(id):
    cursor = mysql.connection.cursor()
    cursor.execute('SELECT * FROM Usuario WHERE id = %s', (id,))
    result = cursor.fetchone()
    cursor.close()
    return jsonify(result), 200 if result else 404

@user.route('/users', methods=['POST'])
def create_usuario():
    data = request.form
    nome = data.get('nome')
    sobrenome = data.get('sobrenome')
    idade = data.get('idade')
    email = data.get('email')
    documento = data.get('documento')
    telefone = data.get('telefone')
    local_de_locacao = data.get('local_de_locacao')
    genero = data.get('genero')
    confirmacao_sms = False

    if nome:
        # Criando o campo 'nome_iniciais' a partir do nome e primeira letra do sobrenome
        if sobrenome:
            nome_iniciais = nome + ' ' + sobrenome[0]
        else:
            nome_iniciais = nome

        cursor = mysql.connection.cursor()
        cursor.execute('INSERT INTO Usuario (nome, nome_iniciais, sobrenome, idade, email, documento, telefone, local_de_locacao, genero, confirmacao_sms) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)',
                       (nome, nome_iniciais, sobrenome, idade, email, documento, telefone, local_de_locacao, genero, confirmacao_sms))
        mysql.connection.commit()
        user_id = cursor.lastrowid  # Obtendo o ID do usuário inserido
        cursor.close()
        return redirect(url_for('user.time_use_page', user_id=user_id))
    else:
        return jsonify({'error': 'O nome do usuário é obrigatório!'}), 400



@user.route('/users/<int:id>', methods=['PUT'])
def update_user(id):
    data = request.get_json()
    nome = data.get('nome')
    nome_iniciais = data.get('nome_iniciais')
    sobrenome = data.get('sobrenome')
    idade = data.get('idade')
    email = data.get('email')
    documento = data.get('documento')
    telefone = data.get('telefone')
    local_de_locacao = data.get('local_de_locacao')
    genero = data.get('genero')
    confirmacao_sms = data.get('confirmacao_sms')

    if nome:
        cursor = mysql.connection.cursor()
        cursor.execute('UPDATE Usuario SET nome = %s, nome_iniciais = %s, sobrenome = %s, idade = %s, email = %s, documento = %s, telefone = %s, local_de_locacao = %s, genero = %s, confirmacao_sms = %s WHERE id = %s',
                       (nome, nome_iniciais, sobrenome, idade, email, documento, telefone, local_de_locacao, genero, confirmacao_sms, id))
        mysql.connection.commit()
        cursor.close()
        return jsonify({'message': 'Usuário atualizado com sucesso!'}), 200
    else:
        return jsonify({'error': 'O nome do usuário é obrigatório!'}), 400

@user.route('/', methods=['GET'])
def welcome_route():
    return render_template('welcome.html')

@user.route('/terms', methods=['GET'])
def terms_page():
    return render_template('terms.html')

@user.route('/sneaker', methods=['GET'])
def sneakers_page():
    return render_template('choose_size.html')

@user.route('/choose-size', methods=['GET', 'POST'])
def choose_size_page():
    if request.method == 'POST':
        size = request.form['size']
        print(size)
        return redirect(url_for('user.time_use_page'))  # Redirect to the next route
    return render_template('choose_size.html')

@user.route('/time_use', methods=['GET', 'POST'])
def time_use_page():
    return render_template('time_use.html')

@user.route('/user_register', methods=['GET'])
def user_register_page():
    return render_template('user_register.html')


@user.route('/sms', methods=['GET'])
def sms_page():
    return render_template('sms_page.html')












