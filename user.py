from flask import Blueprint, request, jsonify, render_template, redirect, url_for, session
from database import mysql
from qrcodeaux import generate_qr_code
from sms_sender import create_verification_code
import io
import base64
from pyzbar.pyzbar import decode
from PIL import Image
import json

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
    sobrenome = nome.split()[-1] if nome else None  # Obtendo o último nome da entrada do nome completo
    data_nascimento = data.get('data_nascimento')
    email = data.get('email')
    documento = data.get('documento')
    telefone = data.get('telefone')
    genero = data.get('genero')
    confirmacao_sms = False

    if nome:
        # Obtendo as iniciais do nome
        if sobrenome:
            nome_iniciais = nome.split()[0] + ' ' + sobrenome[0]
        else:
            nome_iniciais = nome

        cursor = mysql.connection.cursor()
        cursor.execute(
            'INSERT INTO Usuario (nome, nome_iniciais, sobrenome, data_nascimento, email, documento, telefone, genero, confirmacao_sms) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)',
            (nome, nome_iniciais, sobrenome, data_nascimento, email, documento, telefone, genero,
             confirmacao_sms))
        mysql.connection.commit()
        user_id = cursor.lastrowid  # Obtendo o ID do usuário inserido
        cursor.close()
        return user_id
    else:
        return jsonify({'error': 'O nome do usuário é obrigatório!'}), 400





@user.route('/', methods=['GET'])
def welcome_route():
    return render_template('1-welcome-supernova.html')


@user.route('/terms', methods=['GET'])
def terms_page():
    return render_template('2-terms-supernova.html')


@user.route('/sneaker', methods=['GET'])
def sneakers_page():
    return render_template('mock_pages/choose_size.html')


@user.route('/choose-size', methods=['GET', 'POST'])
def choose_size_page():
    if request.method == 'POST':
        size = request.form['size']
        print(size)
        session['size'] = size
        return redirect(url_for('user.time_use_page'))  # Redirect to the next route
    return render_template('3-shoes-size-supernova.html')


@user.route('/time_use', methods=['GET', 'POST'])
def time_use_page():
    return render_template('4-try-shoes-supernova.html')


@user.route('/user_register', methods=['GET', 'POST'])
def user_register_page():
    if request.method == 'POST':
        data = request.form
        print(data)
        user_id = create_user(data)
        session['user_id'] = user_id
        create_verification_code(user_id)
        return redirect(url_for('sms_sender.validate_sms'))
    return render_template('5-register-supernova.html')


@user.route('/qr_code_validation')
def qr_code_validation_page():
    user_id = session.get('user_id')
    if user_id is None:
        user_id = '0000'
    size = session.get('size')
    if size is None:
        size = '0000'
    data = {"user_id": user_id, "size": size}
    qr_code_image = generate_qr_code(data)

    # Salvar a imagem em um buffer de bytes
    img_buffer = io.BytesIO()
    qr_code_image.save(img_buffer, format="PNG")

    # Converter o buffer de bytes em uma string base64
    img_str = base64.b64encode(img_buffer.getvalue()).decode()

    return render_template('7-qr-code-supernova.html', qr_code=img_str)


@user.route('/allright')
def allright_page():
    return render_template('8-ready-try-shoes-supernova.html')


@user.route('/ready')
def ready_page():
    return render_template('9-wear-shoes-supernova.html')


@user.route('/countdownstart')
def countdown_start_page():
    return render_template('10-countdown-try-shoes-supernova.html')


@user.route('/clock')
def clock_page():
    return render_template('11-time-left-shoes-supernova.html')


@user.route('/submit_review', methods=['POST', 'GET'])
def submit_review_page():
    if request.method == 'POST':
        print(request.form)
        comfort = request.form['conforto']
        stability = request.form['estabilidade']
        style = request.form['estilo']
        would_buy = request.form['compraria']
        user_id = session.get('user_id')

        cur = mysql.connection.cursor()
        cur.execute(
            "INSERT INTO Avaliacao (Usuario, conforto, estabilidade, estilo, compraria) VALUES (%s, %s, %s, %s, %s)",
            (user_id, comfort, stability, style, would_buy))
        mysql.connection.commit()
        cur.close()

        return redirect(url_for('user.qrcode_return_page'))

    return render_template('12-rate-try-shoes-supernova.html')


@user.route('/qrcodereturn')
def qrcode_return_page():

    user_id = session.get('user_id')
    if user_id is None:
        user_id = '0000'

    size = session.get('size')
    if size is None:
        size = '0000'
    data = {"user_id": user_id, "size": size}
    qr_code_image = generate_qr_code(data)

    # Salvar a imagem em um buffer de bytes
    img_buffer = io.BytesIO()
    qr_code_image.save(img_buffer, format="PNG")

    # Converter o buffer de bytes em uma string base64
    img_str = base64.b64encode(img_buffer.getvalue()).decode()

    return render_template('13-finish-try-shoes-supernova.html', qr_code=img_str)


@user.route('/thanks')
def thanks_page():
    session.clear()
    return render_template('14-return-shoes-supernova.html')
