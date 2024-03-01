import csv
from datetime import datetime, timedelta

from flask import Blueprint, request, session, redirect, url_for, render_template, make_response

from config.database import mysql

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
        return render_template('admin/7-change-log.html')
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
