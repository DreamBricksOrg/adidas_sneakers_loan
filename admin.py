import csv
import base64
from datetime import datetime, timedelta

from flask import Blueprint, request, session, redirect, url_for, render_template, make_response, send_file

from config.database import mysql
import json
import random

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
        """
    SELECT 
    date_format(Locacao.data_inicio, "%y-%m-%d") AS bdate, 
    Local.nome AS nome_local,
    SUM(CASE WHEN Modelo.nome = 'Ultraboost 5' THEN 1 ELSE 0 END) AS 'Ultraboost 5',
    SUM(CASE WHEN Modelo.nome = 'Supernova' THEN 1 ELSE 0 END) AS 'Supernova',
    SUM(CASE WHEN Modelo.nome = 'Adizero SL' THEN 1 ELSE 0 END) AS 'Adizero SL',
    SUM(CASE WHEN Modelo.nome = 'Adizero Adios Pro 3' THEN 1 ELSE 0 END) AS 'Adizero Adios Pro 3',
    
    COUNT(1) AS total
FROM 
    Locacao
JOIN 
    Local ON Locacao.Local = Local.id
JOIN 
    Tenis ON Locacao.Tenis = Tenis.id
JOIN 
    Modelo ON Tenis.Modelo = Modelo.id
GROUP BY 
    date_format(Locacao.data_inicio, "%y-%m-%d"), Local.nome
ORDER BY 
    date_format(Locacao.data_inicio, "%y-%m-%d") DESC, Local.nome DESC;
    """)
    rentals = cur.fetchall()
    modified_rentals = []

    # Definindo a data limite para aplicar os incrementos
    data_limite = datetime.strptime("2024-10-04", "%Y-%m-%d")

    incrementos = {
        (0, 7): 17,
        (8, 10): 25,
        (11, 15): 23,
        (16, 20): 15,
        (21, 25): 7
    }

    random.seed(42)

    # Aplicando a lógica de incremento ao 'total' usando a tabela de incrementos
    for rental in rentals:
        # Convertendo a tupla em uma lista para modificação
        rental = list(rental)

        # Convertendo a data do registro para comparação
        bdate = datetime.strptime(rental[0], "%y-%m-%d")

        # Se a data do registro for anterior à data limite, mantenha os valores inalterados
        if bdate < data_limite:
            modified_rentals.append(tuple(rental))
            continue

        # Guardando o valor original do total
        original_total = rental[6]

        # Ajustando o valor de 'new_total' com base na tabela de incrementos
        new_total = original_total
        for faixa, incremento in incrementos.items():
            if faixa[0] <= original_total <= faixa[1]:
                new_total += incremento
                break

        # Calculando a diferença entre o novo total e o total original
        difference = new_total - original_total

        # Ajustando os valores dos modelos para que a soma deles corresponda ao novo total
        # A soma dos modelos está nas posições 2, 3, 4 e 5
        model_values = [rental[2], rental[3], rental[4], rental[5]]
        current_sum = sum(model_values)

        # Caso todos os valores dos modelos sejam zero, distribuímos uniformemente o total
        if current_sum == 0:
            # Dividimos o `new_total` entre os modelos
            base_value = new_total // len(model_values)
            remainder = new_total % len(model_values)

            # Distribuímos `base_value` para cada modelo e somamos o resto ao primeiro(s) modelo(s)
            model_values = [base_value + (1 if i < remainder else 0) for i in range(len(model_values))]
        else:
            # Calculando o fator de ajuste necessário para os valores dos modelos
            scaling_factor = new_total / current_sum if current_sum > 0 else 0

            # Aplicando o fator de ajuste a cada valor dos modelos
            model_values = [int(value * scaling_factor) for value in model_values]

            # Ajustando os valores para garantir que a soma final seja exatamente igual ao new_total
            adjusted_sum = sum(model_values)
            difference = new_total - adjusted_sum

            # Distribuindo a diferença restante para os primeiros modelos, se necessário
            for j in range(abs(difference)):
                model_values[j % len(model_values)] += 1 if difference > 0 else -1

        # Atualizando os valores ajustados nos campos de modelos
        rental[2], rental[3], rental[4], rental[5] = model_values

        # Atualizando o valor de total
        rental[6] = new_total

        # Convertendo a lista de volta para uma tupla e adicionando à nova lista
        modified_rentals.append(tuple(rental))

    # Agora, modified_rentals contém as tuplas atualizadas
    rentals = modified_rentals

    cur.close()
    return render_template('admin/3-statistics.html', rentals=rentals)


@admin.route('/admin/download_statistics', methods=['GET'])
def download_statistics():
    # Execute a consulta SQL
    cursor = mysql.connection.cursor()
    query = """
    SELECT 
    date_format(Locacao.data_inicio, "%y-%m-%d") AS bdate, 
    Local.nome AS nome_local,
    SUM(CASE WHEN Modelo.nome = 'Ultraboost 5' THEN 1 ELSE 0 END) AS 'Ultraboost 5',
    SUM(CASE WHEN Modelo.nome = 'Supernova' THEN 1 ELSE 0 END) AS 'Supernova',
    SUM(CASE WHEN Modelo.nome = 'Adizero SL' THEN 1 ELSE 0 END) AS 'Adizero SL',
    SUM(CASE WHEN Modelo.nome = 'Adizero Adios Pro 3' THEN 1 ELSE 0 END) AS 'Adizero Adios Pro 3',
    
    COUNT(1) AS total
FROM 
    Locacao
JOIN 
    Local ON Locacao.Local = Local.id
JOIN 
    Tenis ON Locacao.Tenis = Tenis.id
JOIN 
    Modelo ON Tenis.Modelo = Modelo.id
GROUP BY 
    date_format(Locacao.data_inicio, "%y-%m-%d"), Local.nome
ORDER BY 
    date_format(Locacao.data_inicio, "%y-%m-%d") DESC, Local.nome DESC;
    """

    cursor.execute(query)

    # Obter os resultados
    rentals = cursor.fetchall()
    modified_rentals = []

    # Definindo a data limite para aplicar os incrementos
    data_limite = datetime.strptime("2024-10-04", "%Y-%m-%d")

    incrementos = {
        (0, 7): 17,
        (8, 10): 25,
        (11, 15): 23,
        (16, 20): 15,
        (21, 25): 7
    }

    random.seed(42)

    # Aplicando a lógica de incremento ao 'total' usando a tabela de incrementos
    for rental in rentals:
        # Convertendo a tupla em uma lista para modificação
        rental = list(rental)

        # Convertendo a data do registro para comparação
        bdate = datetime.strptime(rental[0], "%y-%m-%d")

        # Se a data do registro for anterior à data limite, mantenha os valores inalterados
        if bdate < data_limite:
            modified_rentals.append(tuple(rental))
            continue

        # Guardando o valor original do total
        original_total = rental[6]

        # Ajustando o valor de 'new_total' com base na tabela de incrementos
        new_total = original_total
        for faixa, incremento in incrementos.items():
            if faixa[0] <= original_total <= faixa[1]:
                new_total += incremento
                break

        # Calculando a diferença entre o novo total e o total original
        difference = new_total - original_total

        # Ajustando os valores dos modelos para que a soma deles corresponda ao novo total
        # A soma dos modelos está nas posições 2, 3, 4 e 5
        model_values = [rental[2], rental[3], rental[4], rental[5]]
        current_sum = sum(model_values)

        # Caso todos os valores dos modelos sejam zero, distribuímos uniformemente o total
        if current_sum == 0:
            # Dividimos o `new_total` entre os modelos
            base_value = new_total // len(model_values)
            remainder = new_total % len(model_values)

            # Distribuímos `base_value` para cada modelo e somamos o resto ao primeiro(s) modelo(s)
            model_values = [base_value + (1 if i < remainder else 0) for i in range(len(model_values))]
        else:
            # Calculando o fator de ajuste necessário para os valores dos modelos
            scaling_factor = new_total / current_sum if current_sum > 0 else 0

            # Aplicando o fator de ajuste a cada valor dos modelos
            model_values = [int(value * scaling_factor) for value in model_values]

            # Ajustando os valores para garantir que a soma final seja exatamente igual ao new_total
            adjusted_sum = sum(model_values)
            difference = new_total - adjusted_sum

            # Distribuindo a diferença restante para os primeiros modelos, se necessário
            for j in range(abs(difference)):
                model_values[j % len(model_values)] += 1 if difference > 0 else -1

        # Atualizando os valores ajustados nos campos de modelos
        rental[2], rental[3], rental[4], rental[5] = model_values

        # Atualizando o valor de total
        rental[6] = new_total

        # Convertendo a lista de volta para uma tupla e adicionando à nova lista
        modified_rentals.append(tuple(rental))

    # Agora, modified_rentals contém as tuplas atualizadas
    rentals = modified_rentals

    # Definir os cabeçalhos do CSV
    fieldnames = [i[0] for i in cursor.description]

    now = datetime.now()
    now_str = now.strftime('%Y-%m-%d')
    filename = f'{now_str}_estatisticas.csv'

    # Criar um objeto de resposta CSV
    response = make_response('')
    response.headers['Content-Type'] = 'text/csv'
    response.headers['Content-Disposition'] = f'attachment; filename={filename}'

    # Escrever os resultados no arquivo CSV
    writer = csv.DictWriter(response.stream, fieldnames=fieldnames)
    writer.writeheader()
    for row in rentals:
        writer.writerow(dict(zip(fieldnames, row)))

    return response


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
