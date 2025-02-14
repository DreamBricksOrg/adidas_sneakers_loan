import os
from flask import Blueprint, request, jsonify, render_template, redirect, url_for, session, make_response
from config.database import mysql
from dbcrypt import db_encrypt_string
from qrcodeaux import generate_qr_code
from sms_sender import create_verification_code, resend_sms
import io
import base64
from datetime import datetime, timedelta
import execjs
import random

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
    nome_iniciais = data.get('nome_iniciais')
    documento = data.get('documento')
    session['telefone'] = data.get('telefone')
    dados_criptografados = data.get('dados_criptografados')
    telefone_hash = data.get('telefone_hash')
    confirmacao_sms = False

    if nome_iniciais:

        now = datetime.now()
        data_registro = now.strftime('%Y-%m-%d %H:%M:%S')

        cursor = mysql.connection.cursor()
        cursor.execute(
            'INSERT INTO Usuario (nome_iniciais, documento, dados_criptografados, confirmacao_sms, data_registro, telefone_hash) VALUES (%s, %s, %s, %s, %s, %s)',
            (nome_iniciais, documento, dados_criptografados, confirmacao_sms, data_registro, telefone_hash))

        mysql.connection.commit()
        user_id = cursor.lastrowid  # Obtendo o ID do usuário inserido
        cursor.close()
        return user_id
    else:
        return jsonify({'error': 'O nome do usuário é obrigatório!'}), 400


@user.route('/<int:estande>', methods=['GET'])
def index_page(estande):
    if estande:
        session['estande'] = estande
    return render_template('user/1-welcome-supernova.html')


@user.route('/save_user_info', methods=['GET'])
def save_user_info():
    user_id = request.args.get('user_id')
    tenis_id = request.args.get('tenis_id')
    session['user_id'] = user_id
    session['tenis_id'] = tenis_id
    return '', 200


@user.route('/welcome', methods=['GET'])
def welcome_route():
    estande = request.args.get('estande')
    if estande:
        session['estande'] = estande
    return render_template('user/1-welcome-supernova.html')


@user.route('/terms', methods=['GET'])
def terms_page():
    return render_template('user/2-terms-supernova.html')


@user.route('/selectmodel', methods=['GET', 'POST'])
def select_model():
    cur = mysql.connection.cursor()
    cur.execute("SELECT id, nome, status FROM Modelo")
    models = cur.fetchall()
    cur.close()
    if request.method == "POST":
        modelo = request.form['model']
        session['modelo'] = modelo
        return redirect(url_for('user.choose_size_page'))

    return render_template('user/18-select-model.html', models=models)


@user.route('/choose-size', methods=['GET', 'POST'])
def choose_size_page():
    if request.method == 'POST':
        tenis_id = request.form['tenis_id']
        session['tenis_id'] = tenis_id
        return redirect(url_for('user.time_use_page'))

    estande = session.get('estande')
    modelo = session.get('modelo')

    cur = mysql.connection.cursor()
    cur.execute("SELECT id, tamanho, quantidade FROM Tenis WHERE estande = %s AND Modelo = %s", (estande, modelo))
    tenis = cur.fetchall()
    print(tenis)
    cur.close()

    return render_template('user/3-shoes-size-supernova.html', tenis=tenis)


@user.route('/time_use', methods=['GET', 'POST'])
def time_use_page():
    return render_template('user/4-try-shoes-supernova.html')


@user.route('/user_register', methods=['GET', 'POST'])
def user_register_page():
    if request.method == 'POST':
        data = request.form
        user_id = create_user(data)
        session['user_id'] = user_id
        create_verification_code(user_id)
        return redirect(url_for('sms_sender.validate_sms'))
    return render_template('user/5-register-supernova.html')


@user.route('/user_register/searchHash/<telefone_hash>/<telefone>', methods=['POST'])
def search_hash(telefone_hash, telefone):
    cur = mysql.connection.cursor()
    try:
        cur.execute("SELECT * FROM Usuario WHERE telefone_hash = %s", (telefone_hash,))
        data = cur.fetchone()

        if data and data[0]:
            # Atualizar os campos confirmacao_sms, aprovado e retornado para False
            cur.execute("""
                UPDATE Usuario 
                SET confirmacao_sms = %s, aprovado = %s, retornado = %s 
                WHERE telefone_hash = %s
            """, (False, False, False, telefone_hash))
            mysql.connection.commit()

            session['telefone'] = telefone
            session['user_id'] = data[0]
            user_name = data[2]

            return user_name
        else:
            return "", 404
    finally:
        cur.close()


@user.route('/redirect_by_hash_found', methods=['POST'])
def redirect_by_hash_found():
    create_verification_code(session.get('user_id'))
    return "", 204


@user.route('/user_register/checkuser/<user_name>', methods=['GET'])
def user_register_checkuser(user_name):
    return render_template("user/16-check-user-hash.html", user_name=user_name)


@user.route('/user/getuserbycode/', methods=['GET', 'POST'])
def get_user_by_code():
    if request.method == 'POST':
        code = request.form.get('codigo')
        print(code)
        cur = mysql.connection.cursor()
        cur.execute('SELECT Usuario FROM CodigoVerificacao WHERE codigo = %s', (code,))
        user = cur.fetchone()
        if user and user[0]:
            cur.execute(
                'SELECT Locacao.*, Tenis.id FROM Locacao JOIN Tenis ON Locacao.Tenis = Tenis.id WHERE Locacao.Usuario = %s;',
                (user[0],))
            locacao = cur.fetchone()
            if locacao and locacao[0]:
                print(locacao)
                session['user_id'] = locacao[2]
                session['tenis_id'] = locacao[9]
                return redirect(url_for('user.qrcode_return_page'))
        else:
            session['user_id'] = '00'
            session['tenis_id'] = '00'
            return redirect(url_for('user.qrcode_return_page'))
    return render_template('user/17-user-get-code.html')


@user.route('/qr_code_validation', methods=['GET', 'POST'])
def qr_code_validation_page():
    cur = mysql.connection.cursor()
    user_id = session.get('user_id')
    if user_id is None:
        user_id = '00'
    tenis_id = session.get('tenis_id')
    if tenis_id is None:
        tenis_id = '00'
    data = {"user_id": user_id, "tenis_id": tenis_id}
    qr_code_image = generate_qr_code(data)

    # Salvar a imagem em um buffer de bytes
    img_buffer = io.BytesIO()
    qr_code_image.save(img_buffer, format="PNG")

    # Converter o buffer de bytes em uma string base64
    img_str = base64.b64encode(img_buffer.getvalue()).decode()

    if request.method == 'POST':
        cur.execute("SELECT aprovado FROM Usuario WHERE id = %s", (user_id,))
        aprovado = cur.fetchone()
        if aprovado and aprovado[0]:
            return redirect(url_for('user.allright_page'))
        else:
            return '', 403

    return render_template('user/7-qr-code-supernova.html', qr_code=img_str)


@user.route('/allright', methods=['GET', 'POST'])
def allright_page():
    if request.method == 'POST':
        cur = mysql.connection.cursor()
        user_id = session.get('user_id')
        cur.execute("UPDATE Locacao SET status = 'CANCELADO' WHERE Usuario = %s", (user_id,))
        mysql.connection.commit()

        tenis_id = session.get('tenis_id')
        cur.execute('SELECT quantidade FROM Tenis WHERE id = %s', (tenis_id,))
        quantidade = cur.fetchone()

        nova_quantidade = quantidade[0] + 1
        cur.execute('UPDATE Tenis SET quantidade = %s WHERE id = %s', (nova_quantidade, tenis_id))
        mysql.connection.commit()
        return redirect(url_for('user.thanks_page'))

    return render_template('user/8-ready-try-shoes-supernova.html')


@user.route('/ready')
def ready_page():
    user_id = session.get('user_id')
    tenis_id = session.get('tenis_id')

    return render_template('user/9-wear-shoes-supernova.html', user_id=user_id, tenis_id=tenis_id)


@user.route('/countdownstart')
def countdown_start_page():
    return render_template('user/10-countdown-try-shoes-supernova.html')


@user.route('/clock')
def clock_page():
    return render_template('user/11-time-left-shoes-supernova.html')


@user.route('/submit_review', methods=['POST', 'GET'])
def submit_review_page():
    user_id = session.get('user_id')

    if request.method == 'POST':
        cur = mysql.connection.cursor()

        comfort = request.form['rate_confort']
        stability = request.form['rate_stability']
        style = request.form['rate_style']
        would_buy = request.form['rate_buy']

        if user_id is None or not is_int(user_id):
            cur.execute(
                "INSERT INTO Avaliacao (conforto, estabilidade, estilo, compraria) VALUES (%s, %s, %s, %s)",
                (comfort, stability, style, would_buy))
        else:
            cur.execute('SELECT Usuario FROM Avaliacao WHERE Usuario = %s', (user_id,))
            user = cur.fetchone()

            if user:
                cur.close()
                return redirect(url_for('user.qrcode_return_page'))

            cur.execute(
                "INSERT INTO Avaliacao (Usuario, conforto, estabilidade, estilo, compraria) VALUES (%s, %s, %s, %s, %s)",
                (user_id, comfort, stability, style, would_buy))

        mysql.connection.commit()
        cur.close()

        return redirect(url_for('user.qrcode_return_page'))

    return render_template('user/12-rate-try-shoes-supernova.html')


@user.route('/qrcodereturn', methods=['POST', 'GET'])
def qrcode_return_page():
    cur = mysql.connection.cursor()
    user_id = session.get('user_id')
    tenis_id = session.get('tenis_id')
    if user_id is None or tenis_id is None:
        return redirect(url_for('user.get_user_by_code'))

    data = {"user_id": user_id, "tenis_id": tenis_id}
    qr_code_image = generate_qr_code(data)

    # Salvar a imagem em um buffer de bytes
    img_buffer = io.BytesIO()
    qr_code_image.save(img_buffer, format="PNG")

    # Converter o buffer de bytes em uma string base64
    img_str = base64.b64encode(img_buffer.getvalue()).decode()

    if request.method == 'POST':
        cur.execute("SELECT retornado FROM Usuario WHERE id = %s", (user_id,))
        retornado = cur.fetchone()
        if retornado and retornado[0]:
            return redirect(url_for('user.thanks_page'))
        else:
            return '', 403

    return render_template('user/13-finish-try-shoes-supernova.html', qr_code=img_str)


@user.route('/thanks')
def thanks_page():
    session.clear()
    return render_template('user/14-return-shoes-supernova.html')


@user.route('/clearcookie')
def clearcookie_page():
    session.clear()
    return render_template('user/15-clear-cookie.html')


@user.route('/add-user-not-registered', methods=['POST'])
def add_user_not_registered():
    data_list = request.get_json()

    if not isinstance(data_list, list):
        return jsonify({'error': 'Os dados devem ser enviados como uma lista de registros!'}), 400

    cursor = mysql.connection.cursor()
    created_users = []
    errors = []
    pub_key = get_rsa_key()

    for data in data_list:
        try:
            # Validação de campos obrigatórios
            nome = data.get('nome')
            tamanho = data.get('tamanho')
            modelo = data.get('modelo')
            email = data.get('email')
            data_nascimento = data.get('data_nascimento')
            documento = data.get('documento')
            telefone = data.get('telefone', '')
            data_inicio_str = data.get('data_inicio')  # Apenas "dd/mm/aaaa"

            if not all([nome, tamanho, modelo, email, data_nascimento, documento, data_inicio_str]):
                errors.append({'error': 'Campos obrigatórios faltando.', 'data': data})
                continue

            telefone_hash = gerar_hash(telefone) if telefone else None
            confirmacao_sms = False
            genero = "indefinido"

            # Verificação do formato da data de início
            try:
                data_inicio_dt = datetime.strptime(data_inicio_str, "%d/%m/%Y")
            except ValueError:
                errors.append({'error': 'Formato inválido para "data_inicio". Use "dd/mm/aaaa".', 'data': data})
                continue

            # Gerar um horário aleatório entre 07:00 e 12:00
            hora_aleatoria = random.randint(7, 11)
            minuto_aleatorio = random.randint(0, 59)
            data_inicio_dt = data_inicio_dt.replace(hour=hora_aleatoria, minute=minuto_aleatorio)

            # Definir data_fim como 40 minutos após data_inicio
            data_fim_dt = data_inicio_dt + timedelta(minutes=40)

            nome_iniciais = formatar_nome_iniciais(nome)
            if not nome_iniciais:
                errors.append({'error': 'O nome do usuário é inválido!', 'data': data})
                continue

            # Criptografar dados sensíveis
            dataToEncrypt = f"{nome},{email},{data_nascimento},{documento},{telefone},{genero}"
            dados_criptografados = db_encrypt_string(dataToEncrypt, pub_key)

            # Pesquisar o modelo do tênis
            cursor.execute("SELECT id FROM Modelo WHERE nome = %s", (modelo,))
            modelo_result = cursor.fetchone()

            if not modelo_result:
                errors.append({'error': f'Modelo "{modelo}" não encontrado.', 'data': data})
                continue

            modelo_id = modelo_result[0]
            tamanho_formatado = f"U{tamanho}"  # Prefixo "U"

            # Buscar o tênis correspondente
            cursor.execute("SELECT id FROM Tenis WHERE Modelo = %s AND tamanho = %s", (modelo_id, tamanho_formatado))
            tenis_result = cursor.fetchone()

            if not tenis_result:
                errors.append(
                    {'error': f'Nenhum tênis encontrado para o modelo "{modelo}" e tamanho "{tamanho_formatado}".',
                     'data': data})
                continue

            tenis_id = tenis_result[0]  # Pegamos o ID do tênis encontrado

            # Iniciar transação
            cursor.execute(
                '''INSERT INTO Usuario (nome_iniciais, documento, dados_criptografados, confirmacao_sms, data_registro, telefone_hash) 
                VALUES (%s, %s, %s, %s, %s, %s)''',
                (nome_iniciais, documento, dados_criptografados, confirmacao_sms, data_inicio_dt, telefone_hash)
            )
            user_id = cursor.lastrowid

            # Inserir locação na tabela Locacao
            cursor.execute(
                '''INSERT INTO Locacao (Tenis, Usuario, Promotor, Veiculo, Estande, data_inicio, data_fim, status, Local, LocalTreino, TipoTreino) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)''',
                (tenis_id, user_id, 6, 2, 1, data_inicio_dt, data_fim_dt, 'DEVOLVIDO', 1, 2, 2)
            )
            locacao_id = cursor.lastrowid

            # Inserir avaliação para o usuário
            cursor.execute(
                '''INSERT INTO Avaliacao (Usuario, conforto, estabilidade, estilo, compraria) 
                VALUES (%s, %s, %s, %s, %s)''',
                (user_id, 5, 5, 5, 4)
            )
            avaliacao_id = cursor.lastrowid

            # Commit da transação
            mysql.connection.commit()

            created_users.append({
                'id': user_id,
                'nome_iniciais': nome_iniciais,
                'locacao_id': locacao_id,
                'avaliacao_id': avaliacao_id
            })

        except Exception as e:
            mysql.connection.rollback()
            errors.append({'error': str(e), 'data': data})

    cursor.close()

    response = {'created_users': created_users}
    if errors:
        response['errors'] = errors

    return jsonify(response), 201 if created_users else 400


# Função para formatar nome em iniciais
def formatar_nome_iniciais(nome_completo):
    if not nome_completo:
        return ""

    partes = nome_completo.split()

    if len(partes) == 1:
        return partes[0]  # Se houver apenas um nome, retorna sem alteração

    primeiro_nome = partes[0]  # Mantém o primeiro nome completo
    sobrenomes_iniciais = [sobrenome[0] + '.' for sobrenome in partes[1:]]  # Pega a inicial dos outros nomes

    return f"{primeiro_nome} {' '.join(sobrenomes_iniciais)}"


def formatar_data_registro(data_str):
    try:
        # Se a string de data estiver vazia ou None, retorna None
        if not data_str:
            return None

        # Converte o formato "ddmmaaaa HH:MM:SS" para um objeto datetime
        data_obj = datetime.strptime(data_str, "%d%m%Y %H:%M:%S")

        # Retorna no formato "YYYY-MM-DD HH:MM:SS"
        return data_obj.strftime("%Y-%m-%d %H:%M:%S")
    except ValueError:
        return None  # Retorna None se a data estiver inválida


def gerar_hash(telefone):
    hash_val = 0
    if not telefone:
        return hash_val  # Retorna 0 se a string for vazia

    for char in telefone:
        hash_val = ((hash_val << 5) - hash_val) + ord(char)
        hash_val = hash_val & 0xFFFFFFFF  # Converte para inteiro de 32 bits

    return hash_val


def load_js_function():
    JS_FILE_PATH = os.path.join(os.path.dirname(__file__), "static/js/rsa_public_key.js")

    with open(JS_FILE_PATH, "r", encoding="utf-8") as file:
        js_code = file.read()
    return execjs.compile(js_code)


def get_rsa_key():
    js_context = load_js_function()
    rsa_key = js_context.call("getRsaPublicKey")  # Chama a função do JS
    return rsa_key



def is_int(value):
    try:
        int(value)
        return True
    except Exception as e:
        return False
