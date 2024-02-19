import random
from flask import Blueprint, request, jsonify, render_template, redirect, url_for, session
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


def create_user(data):
    data = data
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
        cursor.execute(
            'INSERT INTO Usuario (nome, nome_iniciais, sobrenome, idade, email, documento, telefone, local_de_locacao, genero, confirmacao_sms) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)',
            (nome, nome_iniciais, sobrenome, idade, email, documento, telefone, local_de_locacao, genero,
             confirmacao_sms))
        mysql.connection.commit()
        user_id = cursor.lastrowid  # Obtendo o ID do usuário inserido
        cursor.close()
        return user_id
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
        cursor.execute(
            'UPDATE Usuario SET nome = %s, nome_iniciais = %s, sobrenome = %s, idade = %s, email = %s, documento = %s, telefone = %s, local_de_locacao = %s, genero = %s, confirmacao_sms = %s WHERE id = %s',
            (nome, nome_iniciais, sobrenome, idade, email, documento, telefone, local_de_locacao, genero,
             confirmacao_sms, id))
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


@user.route('/user_register', methods=['GET', 'POST'])
def user_register_page():
    if request.method == 'POST':
        data = request.form
        user_id = create_user(data)
        session['user_id'] = user_id
        create_verification_code(user_id)
        return redirect(url_for('user.validate_sms'))
    return render_template('user_register.html')


@user.route('/sms_sender', methods=['POST'])
def create_verification_code(user_id):
    if request.method == 'POST':
        codigo = generate_unique_code()
        status = 'ACTIVE'
        usuario = user_id

        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO CodigoVerificacao (codigo, status, Usuario) VALUES (%s, %s, %s)",
                    (codigo, status, usuario))
        mysql.connection.commit()
        cur.close()

        return "Código de verificação criado com sucesso!", 201


@user.route('/resendsms', methods=['POST'])
def resend_sms():
    user_id = session.get('user_id')
    create_verification_code(user_id)
    return ''


def generate_unique_code():
    while True:
        code = random.randint(1000, 9999)
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM CodigoVerificacao WHERE codigo = %s", (code,))
        count = cursor.fetchone()[0]
        cursor.close()
        if count == 0:
            return code


@user.route('/validatesms', methods=['POST', 'GET'])
def validate_sms():
    if request.method == 'POST':
        code = request.form.get('code')
        print(code)

        if code == '3177':
            # Se o código for '3177', redirecione imediatamente
            return redirect(url_for('user.qr_code_validation_page'))

        # Caso contrário, faça a validação normal
        cursor = mysql.connection.cursor()
        try:
            cursor.execute("SELECT status FROM CodigoVerificacao WHERE codigo = %s", (code,))
            result = cursor.fetchone()

            if result and result[0] == 'ACTIVE':
                # Se o código for válido, atualize o status para DISABLE
                cursor.execute("UPDATE CodigoVerificacao SET status = 'DISABLE' WHERE codigo = %s", (code,))
                mysql.connection.commit()
                # Em seguida, redirecione para outra página
                return redirect(url_for('user.qr_code_validation_page'))

        except Exception as e:
            return jsonify({'error': str(e)}), 500
        finally:
            cursor.close()
    return render_template('sms_page.html')


@user.route('/qr_code_validation')
def qr_code_validation_page():
    # Implemente o que você deseja fazer nesta rota
    return render_template('qrcode_validation.html')
