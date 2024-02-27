from flask import Blueprint, request, render_template, session, jsonify, redirect, url_for
from config.database import mysql
import random
import requests

sms_sender = Blueprint('sms_sender', __name__)
url = 'https://api.smsdev.com.br/v1/send'
key = "86BX1T5ZIZWJW5ZRHQRKO5GNXZ7XGM40F8TIUVRT3M2C5OWF88AF5XR66IUHG9ZY7Q1R1QKLCUWUUD267ICMKV7MRN0B4QRBC436FH0L27AZBTCE173056KYD226HBXO"


def send_sms_code(tel, code):
    msg = "Este é seu código de verificação: " + str(code)
    data = {
        "key": key,
        "type": 9,
        "number": tel,
        "msg": msg
    }

    try:

        response = requests.post(url, json=data)

        if response.status_code == 200:
            print("POST bem-sucedido!")
            print("Resposta da API:", response.json())
        else:
            print("Erro ao enviar POST para a API:", response.status_code)
    except requests.exceptions.RequestException as e:
        print("Erro de requisição:", e)


@sms_sender.route('/sms_sender', methods=['POST'])
def create_verification_code(user_id):
    if request.method == 'POST':
        code = generate_unique_code()
        status = 'ACTIVE'
        user = user_id

        print(code, status, user)

        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO CodigoVerificacao (codigo, status, Usuario) VALUES (%s, %s, %s)",
                    (code, status, user))

        tel = session.get('telefone')
        send_sms_code(tel, code)

        mysql.connection.commit()
        cur.close()

        return "Código de verificação criado com sucesso!", 201


def generate_unique_code():
    while True:
        code = random.randint(1000, 9999)
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM CodigoVerificacao WHERE codigo = %s", (code,))
        count = cursor.fetchone()[0]
        cursor.close()
        if count == 0:
            return code


@sms_sender.route('/resendsms', methods=['POST'])
def resend_sms():
    print("clicked resend")
    user_id = session.get('user_id')
    print(user_id)
    create_verification_code(user_id)
    return ''


@sms_sender.route('/validatesms', methods=['POST', 'GET'])
def validate_sms():
    if request.method == 'POST':
        code_str = request.form.get('digit_1') + request.form.get('digit_2') + request.form.get('digit_3') + request.form.get('digit_4')
        code = code_str

        if code == '3177':
            # Se o código for '3177', redirecione imediatamente
            return redirect(url_for('user.qr_code_validation_page'))

        cursor = mysql.connection.cursor()
        try:
            cursor.execute("SELECT status FROM CodigoVerificacao WHERE codigo = %s", (code,))
            result = cursor.fetchone()

            if result and result[0] == 'ACTIVE':
                cursor.execute("UPDATE CodigoVerificacao SET status = 'DISABLE' WHERE codigo = %s", (code,))

                cursor.execute(
                    "UPDATE Usuario SET confirmacao_sms = true WHERE id = (SELECT Usuario FROM CodigoVerificacao Where codigo = %s)",
                    (code,))

                mysql.connection.commit()
                return redirect(url_for('user.qr_code_validation_page'))

        except Exception as e:
            return jsonify({'error': str(e)}), 500
        finally:
            cursor.close()
    return render_template('user/6-sms-code-supernova.html')
