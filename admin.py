import csv
import base64
from datetime import datetime, timedelta

from flask import Blueprint, request, session, redirect, url_for, render_template, make_response, send_file

from config.database import mysql
import json

admin = Blueprint('admin', __name__)


@admin.route('/admin/login', methods=['POST', 'GET'])
def admin_login_page():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM Promotor WHERE usuario = %s AND senha = %s", (username, password))
        promotor = cur.fetchone()
        cur.close()

        if promotor and promotor[1] == 'admin':
            session['logged_in'] = True
            session['admin_id'] = promotor[0]
            return redirect(url_for('admin.admin_menu_page'))
        else:
            return redirect(url_for('admin.admin_login_page'))

    return render_template('admin/1-admin-login.html')


@admin.route('/admin/menu')
def admin_menu_page():
    if 'logged_in' in session and session['logged_in']:
        return render_template('admin/2-admin-menu.html')
    else:
        return redirect(url_for('admin.admin_login_page'))


@admin.route('/admin/statistics', methods=['GET'])
def statistics_page():
    cur = mysql.connection.cursor()
    cur.execute(
        'SELECT date_format(data_inicio, "%y-%m-%d") as bdate, adidas_prod.Local.nome nome_local, count(1) as numrentals '
        'FROM adidas_prod.Locacao, adidas_prod.Local '
        'WHERE adidas_prod.Locacao.Local = adidas_prod.Local.id '
        'group by date_format(data_inicio, "%y-%m-%d"), adidas_prod.Local.nome '
        'order by date_format(data_inicio, "%y-%m-%d") desc, adidas_prod.Local.nome desc;')
    rentals = cur.fetchall()

    cur.close()
    return render_template('admin/3-statistics.html', rentals=rentals)


@admin.route('/admin/generatekeys', methods=['GET'])
def generate_keys_page():
    if 'logged_in' in session and session['logged_in']:
        return render_template('admin/4-generate-keys.html')
    else:
        return redirect(url_for('admin.admin_login_page'))


@admin.route('/admin/usersdata', methods=['GET'])
def users_data_page():
    if 'logged_in' in session and session['logged_in']:
        return render_template('admin/5-users-data.html')
    else:
        return redirect(url_for('admin.admin_login_page'))


@admin.route('/admin/logmudancas', methods=['GET'])
def log_mudancas_page():
    if 'logged_in' in session and session['logged_in']:
        return render_template('admin/6-change-log.html')
    else:
        return redirect(url_for('admin.admin_login_page'))


@admin.route('/admin/downloadlogchanges', methods=['GET'])
def download_log_changes():
    cursor = mysql.connection.cursor()
    cursor.execute(
        "SELECT Promotor.nome AS Promotor, Local.nome AS Local, Tenis.tamanho AS Tenis, "
        "quantidadeOriginal, quantidadeNova, data "
        "FROM LogTenis "
        "JOIN Promotor ON LogTenis.Promotor = Promotor.id "
        "JOIN Tenis ON LogTenis.tamanho = Tenis.id "
        "JOIN Local ON LogTenis.Local = Local.id; ")

    # Obter os resultados
    results = cursor.fetchall()

    # Definir os cabeçalhos do CSV
    fieldnames = [i[0] for i in cursor.description]

    now = datetime.now()
    now_str = now.strftime('%Y-%m-%d')
    filename = f'{now_str}_log_mudancas.csv'

    # Criar um objeto de resposta CSV
    response = make_response('')
    response.headers['Content-Type'] = 'text/csv'
    response.headers['Content-Disposition'] = f'attachment; filename={filename}'

    # Escrever os resultados no arquivo CSV
    writer = csv.DictWriter(response.stream, fieldnames=fieldnames)
    writer.writeheader()
    for row in results:
        writer.writerow(dict(zip(fieldnames, row)))

    return response


@admin.route('/admin/downloadcryptedcsv', methods=['GET'])
def download_users_data_csv():
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT Usuario.id,"
                   " Usuario.dados_criptografados,"
                   " Tenis.tamanho AS Tenis,"
                   " Locacao.data_inicio AS Inicio,"
                   " Locacao.data_fim AS Fim,"
                   " Usuario.confirmacao_sms,"
                   " Locacao.status AS Status,"
                   " Promotor.nome as promotor,"
                   " Locacao.Estande,"
                   " Local.nome AS Local"
                   " FROM Locacao JOIN Tenis "
                   "ON Locacao.Tenis = Tenis.id JOIN Usuario "
                   "ON Locacao.Usuario = Usuario.id JOIN Promotor "
                   "ON Locacao.Promotor = Promotor.id JOIN Local "
                   "ON Locacao.Local = Local.id ORDER BY Locacao.data_inicio DESC;")

    # Obter os resultados
    results = cursor.fetchall()

    # Definir os cabeçalhos do CSV
    fieldnames = [i[0] for i in cursor.description]

    now = datetime.now()
    now_str = now.strftime('%Y-%m-%d')
    filename = 'crypted.csv'

    # Criar um objeto de resposta CSV
    response = make_response('')
    response.headers['Content-Type'] = 'text/csv'
    response.headers['Content-Disposition'] = f'attachment; filename={filename}'

    writer = csv.DictWriter(response.stream, fieldnames=fieldnames)
    writer.writeheader()
    for row in results:
        writer.writerow(dict(zip(fieldnames, row)))

    return response


@admin.route('/downloadencryptedblob', methods=['POST'])
def download_blob():
    user_id = request.form['user_id']
    cur = mysql.connection.cursor()

    # Executar a consulta SQL para recuperar os dados BLOB
    cur.execute("SELECT documento, retrato FROM Fotos WHERE Usuario = %s", (user_id,))
    data = cur.fetchone()

    if data:
        documento_blob = data[0]
        retrato_blob = data[1]

        # Codificar os bytes em base64
        documento_base64 = base64.b64encode(documento_blob).decode('utf-8')
        retrato_base64 = base64.b64encode(retrato_blob).decode('utf-8')

        response_data = {
            "documento_bytes": documento_base64,
            "retrato_bytes": retrato_base64
        }
        return json.dumps(response_data)
    else:
        return json.dumps({"error": "Dados não encontrados para o usuário fornecido."}), 404


@admin.route('/admin')
def redirect_admin():
    return redirect(url_for('admin.admin_login_page'))


@admin.route('/alive', methods=['GET'])
def is_alive():
    return "YES"