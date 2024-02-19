from flask import Blueprint, request, render_template, session, jsonify, redirect, url_for
from database import mysql
import random

sms_sender = Blueprint('sms_sender', __name__)

@sms_sender.route('/sms_sender', methods=['POST'])
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
    user_id = session.get('user_id')
    create_verification_code(user_id)
    return ''


@sms_sender.route('/validatesms', methods=['POST', 'GET'])
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
