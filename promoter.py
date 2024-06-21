import MySQLdb
from flask import Blueprint, request, jsonify, render_template, redirect, url_for, session, make_response
from config.database import mysql
from datetime import datetime
import csv

promoter = Blueprint('promoter', __name__)


@promoter.route('/promoter/start', methods=['GET', 'POST'])
def promoter_scan_start_page():
    if request.method == 'POST':
        estande = request.form['estande']
        session['estande'] = estande
        return redirect(url_for('promoter.promoter_login_page'))

    return render_template('promoter/1-scan-start.html')


@promoter.route('/promotor/inicio', methods=['GET', 'POST'])
def promoter_scan_start_page_pt():
    if request.method == 'POST':
        estande = request.form['estande']
        session['estande'] = estande
        return redirect(url_for('promoter.promoter_login_page'))

    return render_template('promoter/1-scan-start.html')


@promoter.route('/promoter/login', methods=['POST', 'GET'])
def promoter_login_page():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM Promotor WHERE usuario = %s AND senha = %s", (username, password))
        promotor = cur.fetchone()

        cur.close()

        if promotor:
            session['logged_in'] = True
            session['promoter_id'] = promotor[0]
            return redirect(url_for('promoter.promoter_local_page'))
        else:
            return redirect(url_for('promoter.promoter_login_page'))

    return render_template('promoter/2-promoter-login.html')


@promoter.route('/promoter/local', methods=['GET', 'POST'])
def promoter_local_page():
    if request.method == 'POST':
        local_id = request.form['local']
        session['local_id'] = local_id
        return redirect(url_for('promoter.available_shoes_page', model="1"))
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM Local")
    locais = cur.fetchall()
    cur.close()
    if 'logged_in' in session and session['logged_in'] and session['estande'] and session['promoter_id']:
        return render_template('promoter/3-local-confirmation.html', locais=locais)
    else:
        return redirect(url_for('promoter.error_page'))


@promoter.route('/promoter/availableshoes/<model>', methods=['GET', 'POST'])
def available_shoes_page(model):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM Modelo")
    models = cur.fetchall()

    cur.execute("SELECT id, tamanho, quantidade FROM Tenis WHERE Estande = %s AND Modelo = %s",
                (session.get('estande'), model))
    tenis_disponiveis = cur.fetchall()
    cur.close()
    if 'logged_in' in session and session['logged_in'] and session['estande'] and session['promoter_id']:
        return render_template('promoter/4-available-shoes.html', tenis_disponiveis=tenis_disponiveis, models=models)
    else:
        return redirect(url_for('promoter.error_page'))


@promoter.route('/promoter/availableshoes', methods=['POST'])
def available_shoes_page_post():
    if request.method == 'POST':
        promoter_id = session.get('promoter_id')
        local_id = session.get('local_id')

        cur = mysql.connection.cursor()
        for i in range(1, len(request.form) // 3 + 1):
            corrigir = request.form.get(f'corrigir_quantidade_{i}', '').strip()
            tenis_id = request.form.get(f'tenis_id_{i}')
            quantidade_antiga = request.form.get(f'quantidade_antiga_{i}')
            now = datetime.now()
            change_date = now.strftime('%Y-%m-%d %H:%M:%S')

            if corrigir:
                cur.execute("UPDATE Tenis SET quantidade = %s WHERE id = %s", (corrigir, tenis_id))
                mysql.connection.commit()

                cur.execute(
                    "INSERT INTO LogTenis (Promotor, Local, Tenis, quantidadeOriginal, quantidadeNova, data) VALUES (%s, %s, %s, %s, %s, %s)",
                    (promoter_id, local_id, tenis_id, quantidade_antiga, corrigir, change_date))
                mysql.connection.commit()
        cur.close()
        return redirect(url_for('promoter.promoter_menu_page'))


@promoter.route('/promoter/ready-start')
def ready_start_page():
    return render_template('promoter/5-ready-start.html')


@promoter.route('/promoter/menu')
def promoter_menu_page():
    if 'logged_in' in session and session['logged_in'] and session['estande'] and session['promoter_id']:
        return render_template('promoter/6-promoter-menu.html')
    else:
        return redirect(url_for('promoter.error_page'))


@promoter.route('/promoter/rentallist', methods=['GET', 'POST'])
def rental_list_page():
    if request.method == 'POST':
        return redirect(url_for('promoter.promoter_menu_page'))

    local_id = session.get('local_id')

    if local_id is None:
        return redirect(url_for('promoter.error_page'))

    # Convert local_id to the correct type if necessary
    try:
        local_id = int(local_id)  # or str(local_id) if it's supposed to be a string
    except ValueError:
        return redirect(url_for('promoter.error_page'))

    cur = mysql.connection.cursor()

    query = """
    SELECT Locacao.id, 
           Tenis.tamanho AS Tenis, 
           Usuario.nome_iniciais AS Usuario, 
           Promotor.nome AS Promotor, 
           DATE_FORMAT(Locacao.data_inicio, "%%d/%%m/%%Y %%H:%%i:%%s") AS Inicio, 
           DATE_FORMAT(Locacao.data_fim, "%%d/%%m/%%Y %%H:%%i:%%s") AS Fim, 
           Locacao.status AS Status, 
           Local.nome AS Local, 
           Locacao.Estande, 
           Usuario.id, 
           Modelo.nome AS Modelo, 
           Tenis.id
    FROM Locacao 
    JOIN Tenis ON Locacao.Tenis = Tenis.id 
    JOIN Usuario ON Locacao.Usuario = Usuario.id 
    JOIN Promotor ON Locacao.Promotor = Promotor.id 
    JOIN Local ON Locacao.Local = Local.id 
    JOIN Modelo ON Tenis.Modelo = Modelo.id 
    WHERE Local.id = %s 
    ORDER BY Locacao.data_inicio DESC;
    """

    try:
        cur.execute(query, (local_id,))
        rentals = cur.fetchall()
        print(rentals)
    except MySQLdb.ProgrammingError as e:
        print(f"An error occurred: {e}")
        return redirect(url_for('promoter.error_page'))
    finally:
        cur.close()

    if 'logged_in' in session and session['logged_in'] and session['estande'] and session['promoter_id']:
        return render_template('promoter/7-rental-list.html', rentals=rentals)
    else:
        return redirect(url_for('promoter.error_page'))


@promoter.route('/promoter/updatevalue', methods=['POST'])
def update_values():
    data = request.json
    tamanho = data.get('tamanho')
    action = data.get('action')

    cur = mysql.connection.cursor()
    cur.execute('SELECT quantidade FROM Tenis WHERE tamanho = %s', (tamanho,))

    resultado = cur.fetchone()

    if resultado:
        if action == 'increase':
            nova_quantidade = resultado[0] + 1
        elif action == 'decrease':
            if resultado > 0:
                nova_quantidade = resultado[0] - 1
        else:
            return "Ação inválida. Use 'increase' ou 'decrease'."

        cur.execute('UPDATE Tenis SET quantidade = %s WHERE tamanho = %s', (nova_quantidade, tamanho))
        mysql.connection.commit()
        cur.close()
        return f'Quantidade para o tamanho {tamanho} atualizada para {nova_quantidade}\n'

    return redirect(url_for('promoter.promoter_menu_page'))


@promoter.route('/promoter/update_rental', methods=['POST'])
def update_rental():
    data = request.json
    oldValue = data.get('oldValue')
    newValue = data.get('newValue')
    rental_id = data.get('rental_id')

    # Connect to the database
    cur = mysql.connection.cursor()

    # Find the ID of the old tennis
    cur.execute('SELECT id FROM Tenis WHERE tamanho = %s', (oldValue,))
    old_tennis_id = cur.fetchone()

    if not old_tennis_id:
        cur.close()
        return jsonify({'message': 'Old size not found'}), 404

    # Find the ID of the new tennis
    cur.execute('SELECT id FROM Tenis WHERE tamanho = %s', (newValue,))
    new_tennis_id = cur.fetchone()

    if not new_tennis_id:
        cur.close()
        return jsonify({'message': 'New size not found'}), 404

    # Update records in the 'Rental' table with the new tennis ID
    cur.execute('UPDATE Locacao SET Tenis = %s WHERE Tenis = %s AND id = %s',
                (new_tennis_id[0], old_tennis_id[0], rental_id))
    mysql.connection.commit()

    cur.close()
    return jsonify({'message': 'Locacao updated successfully'}), 200


@promoter.route('/promoter/scanaproverental', methods=['GET', 'POST'])
def scan_aprove_rental_page():
    if request.method == 'POST':
        user_id = request.form['user_id']
        tenis_id = request.form['tenis_id']
        session['user_id'] = user_id
        session['tenis_id'] = tenis_id
        return redirect(url_for('promoter.check_user_size_page'))
    if 'logged_in' in session and session['logged_in'] and session['estande'] and session['promoter_id']:
        return render_template('promoter/8-scan-aprove-rental.html')
    else:
        return redirect(url_for('promoter.error_page'))


@promoter.route('/promoter/checkuser', methods=['GET'])
def check_user_size_page():
    user_id = session['user_id']
    tenis_id = session['tenis_id']

    cur = mysql.connection.cursor()
    cur.execute("SELECT Usuario.nome_iniciais "
                "FROM Usuario "
                "WHERE Usuario.id = %s;", (user_id,))
    result = cur.fetchone()

    cur.execute("SELECT Modelo, tamanho FROM Tenis WHERE id = %s", (tenis_id,))
    tenis = cur.fetchone()
    size = tenis[1]
    model_id = tenis[0]

    cur.execute("SELECT nome FROM Modelo WHERE id = %s", (model_id,))
    model_result = cur.fetchone()
    model = model_result[0]


    cur.close()

    if not result:
        cur.close()
        return redirect(url_for('promoter.error_user_not_found_page'), 404)

    now = datetime.now()
    start_date = now.strftime('%Y-%m-%d %H:%M:%S')

    if 'logged_in' in session and session['logged_in'] and session['estande'] and session['promoter_id']:
        return render_template('promoter/15-check-user.html', user_name=result[0], model=model, size=size, start_date=start_date)
    else:
        return redirect(url_for('promoter.error_page'))


@promoter.route('/promoter/captureid', methods=['GET', 'POST'])
def capture_id():
    if request.method == 'POST':
        files = request.files
        file = files.get('file')

        user_id = session['user_id']
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO Fotos (Usuario, documento) VALUES(%s, %s)", (user_id, file.read(),))
        mysql.connection.commit()
        cur.close()

        return redirect(url_for('promoter.capture_portrait'))

    if 'logged_in' in session and session['logged_in'] and session['estande'] and session['promoter_id']:
        return render_template('promoter/13-capture-id.html')
    else:
        return redirect(url_for('promoter.error_page'))


@promoter.route('/promoter/captureportrait', methods=['GET', 'POST'])
def capture_portrait():
    if request.method == 'POST':
        files = request.files
        file = files.get('file')

        user_id = session['user_id']

        cur = mysql.connection.cursor()
        # cur.execute("INSERT INTO Fotos (Usuario, documento, retrato) VALUES(%s)", (user_id, id_file.read(), file.read(),))
        cur.execute("UPDATE Fotos SET retrato = %s WHERE Usuario = %s", (file.read(), user_id,))
        mysql.connection.commit()
        cur.close()

        return redirect(url_for('promoter.aprove_rental_page'))

    if 'logged_in' in session and session['logged_in'] and session['estande'] and session['promoter_id']:
        return render_template('promoter/14-capture-portrait.html')
    else:
        return redirect(url_for('promoter.error_page'))


@promoter.route('/promoter/aproverental', methods=['GET', 'POST'])
def aprove_rental_page():
    cur = None
    try:
        cur = mysql.connection.cursor()

        tenis_id = session.get('tenis_id')
        user_id = session.get('user_id')
        promoter_id = session.get('promoter_id')
        local_id = session.get('local_id')
        estande = session.get('estande')
        print(f'LOG: /promoter/aproverental - session(tenis_id: {tenis_id}, user_id:{user_id}, '
              f'promoter_id:{promoter_id}, local_id:{local_id}), estande:{estande}')

        cur.execute('SELECT nome FROM Local WHERE id = %s', (local_id,))
        local = cur.fetchone()
        print(f'LOG: /promoter/aproverental - local: {local[0] if local is not None else "None"}')

        now = datetime.now()
        data_inicio = now.strftime('%Y-%m-%d %H:%M:%S')

        data_fim = None

        status = 'ALOCADO'

        cur.execute("SELECT Modelo, tamanho FROM Tenis WHERE id = %s", (tenis_id,))
        tenis = cur.fetchone()
        size = tenis[1]
        model_id = tenis[0]

        cur.execute("SELECT nome FROM Modelo WHERE id = %s", (model_id,))
        model_result = cur.fetchone()
        model = model_result[0]

        print(f'LOG: /promoter/aproverental - tenis_id: {tenis_id if tenis_id is not None else "None"} ')

        if request.method == 'POST':
            # cur.execute('SELECT Usuario FROM Locacao WHERE Usuario = %s', (user_id,))
            # result = cur.fetchone()

            # if result:
            #     print(
            #         f'ERROR: /promoter/aproverental - usuario_id: {result[0] if result is not None else "None"} already exists!')

            # else:
            cur.execute(
                'INSERT INTO Locacao (Tenis, Usuario, Promotor, Local, Estande, data_inicio, data_fim, status) VALUES ( %s, %s, %s, %s, %s, %s, %s, %s)',
                (tenis_id[0], user_id, promoter_id, local_id, estande, data_inicio, data_fim, status))
            mysql.connection.commit()

            if cur.lastrowid != 0:
                cur.execute('SELECT quantidade FROM Tenis WHERE id = %s', (tenis_id,))
                quantidade = cur.fetchone()
                if quantidade[0] > 0:
                    nova_quantidade = quantidade[0] - 1
                    cur.execute('UPDATE Tenis SET quantidade = %s WHERE id = %s', (nova_quantidade, tenis_id))
                    mysql.connection.commit()

                cur.execute('SELECT id FROM Usuario WHERE id = %s', (user_id,))
                user = cur.fetchone()
                if user:
                    cur.execute('UPDATE Usuario SET aprovado = true WHERE id = %s', (user_id,))
                    mysql.connection.commit()

                cur.execute('UPDATE Usuario SET local_de_locacao = %s WHERE id = %s', (local[0], user_id))
                mysql.connection.commit()
            return redirect(url_for('promoter.rental_list_page'))

        cur.execute("SELECT nome_iniciais FROM Usuario WHERE id = %s ", (user_id,))
        user_name = cur.fetchone()
        if 'logged_in' in session and session['logged_in'] and session['estande'] and session['promoter_id']:
            return render_template('promoter/9-aprove-rental.html', user_name=user_name[0], start_date=data_inicio,
                                   size=size, model=model)
        else:
            return redirect(url_for('promoter.error_page'))

    except Exception as e:
        print(f'ERROR: {str(e)}')
        return redirect(url_for('promoter.error_page'))

    finally:
        if cur is not None:
            cur.close()


@promoter.route('/promoter/scanreturn', methods=['GET', 'POST'])
def scan_return_page():
    if request.method == 'POST':
        user_id = request.form['user_id']
        tenis_id = request.form['tenis_id']
        session['user_id'] = user_id
        session['tenis_id'] = tenis_id

        return redirect(url_for('promoter.return_page'))
    if 'logged_in' in session and session['logged_in'] and session['estande'] and session['promoter_id']:
        return render_template('promoter/10-scan-return.html')
    else:
        return redirect(url_for('promoter.error_page'))


@promoter.route('/promoter/scanreturnbtn', methods=['GET', 'POST'])
def scan_return_btn():
    if request.method == 'POST':
        user_id = request.json['user_id']
        tenis_id = request.json['tenis_id']
        session['user_id'] = user_id
        session['tenis_id'] = tenis_id
        return redirect(url_for('promoter.return_page'))
    if 'logged_in' in session and session['logged_in'] and session['estande'] and session['promoter_id']:
        return render_template('promoter/10-scan-return.html')
    else:
        return redirect(url_for('promoter.error_page'))


@promoter.route('/promoter/return', methods=['GET', 'POST'])
def return_page():
    user_id = session.get('user_id')
    tenis_id = session.get('tenis_id')

    cur = mysql.connection.cursor()
    cur.execute("SELECT Modelo, tamanho FROM Tenis WHERE id = %s", (tenis_id,))
    tenis = cur.fetchone()
    model_id = tenis[0]
    size = tenis[1]

    cur.execute("SELECT nome FROM Modelo WHERE id = %s", (model_id,))
    model_result = cur.fetchone()
    model = model_result[0]

    cur.execute("""
        SELECT U.nome_iniciais, L.Tenis, L.data_inicio, L.status
        FROM Usuario U, Locacao L
        WHERE U.id = L.Usuario
        AND U.id = %s
        ORDER BY L.data_inicio DESC
        LIMIT 1;
    """, (user_id,))

    locacao = cur.fetchone()

    if request.method == 'POST':
        if locacao[3] == 'ALOCADO' or locacao[3] == 'VENCIDO':

            cur.execute('SELECT quantidade FROM Tenis WHERE id = %s', (tenis_id,))
            quantidade = cur.fetchone()

            nova_quantidade = quantidade[0] + 1
            cur.execute('UPDATE Tenis SET quantidade = %s WHERE id = %s', (nova_quantidade, tenis_id))
            mysql.connection.commit()

            now = datetime.now()
            end_date = now.strftime('%Y-%m-%d %H:%M:%S')

            cur.execute("UPDATE Locacao SET status = 'DEVOLVIDO', data_fim = %s WHERE Usuario = %s",
                        (end_date, user_id))
            mysql.connection.commit()

            cur.execute('SELECT id FROM Usuario WHERE id = %s', (user_id,))
            user = cur.fetchone()

            if user:
                cur.execute('UPDATE Usuario SET retornado = true WHERE id = %s', (user_id,))
                mysql.connection.commit()

        cur.close()
        return redirect(url_for('promoter.promoter_menu_page'))

    cur.close()

    if not locacao:
        cur.close()
        return redirect(url_for('promoter.error_user_not_found_page'), 404)

    end_date = datetime.now()
    start_date = locacao[2]
    duration = end_date - start_date
    duration_minutes = int(duration.total_seconds() / 60)

    if 'logged_in' in session and session['logged_in'] and session['estande'] and session['promoter_id']:
        return render_template('promoter/11-return.html', user_name=locacao[0], size=size, model=model, start_date=start_date,
                               duration=duration_minutes)
    else:
        return redirect(url_for('promoter.error_page'))


@promoter.route('/promoter/returnwithproblems', methods=['GET', 'POST'])
def return_with_problems_page():
    user_id = session.get('user_id')
    tenis_id = session.get('tenis_id')

    cur = mysql.connection.cursor()
    cur.execute("SELECT Modelo, tamanho FROM Tenis WHERE id = %s", (tenis_id,))
    tenis = cur.fetchone()
    model = tenis[0]
    size = tenis[1]

    cur.execute("SELECT U.nome_iniciais, L.Tenis, L.data_inicio, L.status "
                "FROM Usuario U, Locacao L "
                "WHERE U.id = L.Usuario "
                "AND U.id = %s;", (user_id,))

    locacao = cur.fetchone()

    if request.method == 'POST':
        if locacao[3] == 'ALOCADO' or locacao[3] == 'VENCIDO':

            now = datetime.now()
            end_date = now.strftime('%Y-%m-%d %H:%M:%S')

            cur.execute("UPDATE Locacao SET status = 'DEVOLVIDO', data_fim = %s WHERE Usuario = %s",
                        (end_date, user_id))
            mysql.connection.commit()

            cur.execute('SELECT id FROM Usuario WHERE id = %s', (user_id,))
            user = cur.fetchone()

            if user:
                cur.execute('UPDATE Usuario SET retornado = true WHERE id = %s', (user_id,))
                mysql.connection.commit()

        cur.close()
        return redirect(url_for('promoter.promoter_menu_page'))

    cur.close()

    if not locacao:
        cur.close()
        return redirect(url_for('promoter.error_user_not_found_page'), 404)

    end_date = datetime.now()
    start_date = locacao[2]
    duration = end_date - start_date
    duration_minutes = int(duration.total_seconds() / 60)

    if 'logged_in' in session and session['logged_in'] and session['estande'] and session['promoter_id']:
        return render_template('promoter/11-return.html', user_name=locacao[0], size=size, model=model, start_date=start_date,
                               duration=duration_minutes)
    else:
        return redirect(url_for('promoter.error_page'))


@promoter.route('/promoter/rentallistexpired', methods=['GET', 'POST'])
def rental_list_expired_page():
    if request.method == 'POST':
        session.clear()
        return redirect(url_for('promoter.promoter_scan_start_page'))

    local_id = session.get('local_id')

    cur = mysql.connection.cursor()
    cur.execute("SELECT Locacao.id, Tenis.tamanho AS Tenis, Usuario.nome_iniciais AS Usuario, "
                "Promotor.nome AS Promotor, Locacao.data_inicio AS Inicio, Locacao.data_fim AS Fim, "
                "Locacao.status AS Status, Local.nome AS Local, Locacao.Estande, Usuario.id "
                "FROM Locacao "
                "JOIN Tenis ON Locacao.Tenis = Tenis.id "
                "JOIN Usuario ON Locacao.Usuario = Usuario.id "
                "JOIN Promotor ON Locacao.Promotor = Promotor.id "
                "JOIN Local ON Locacao.Local = Local.id "
                "WHERE Local = %s "
                "ORDER BY Locacao.data_inicio DESC;", (local_id,))
    rentals = cur.fetchall()
    cur.close()
    if 'logged_in' in session and session['logged_in'] and session['estande'] and session['promoter_id']:
        return render_template('promoter/12-expired-list.html', rentals=rentals)
    else:
        return redirect(url_for('promoter.error_page'))


@promoter.route('/promoter/baixar_csv', methods=['GET'])
def baixar_csv():
    # Execute a consulta SQL
    cursor = mysql.connection.cursor()
    cursor.execute(
        "SELECT Locacao.id, Tenis.tamanho AS Tenis, Usuario.nome_iniciais AS Usuario, Promotor.nome AS Promotor, "
        "Locacao.data_inicio AS Inicio, Locacao.data_fim AS Fim, Locacao.status AS Status, Local.nome AS Local, "
        "Locacao.Estande FROM Locacao JOIN Tenis ON Locacao.Tenis = Tenis.id JOIN Usuario ON Locacao.Usuario = Usuario.id "
        "JOIN Promotor ON Locacao.Promotor = Promotor.id JOIN Local ON Locacao.Local = Local.id;")

    # Obter os resultados
    results = cursor.fetchall()

    # Definir os cabeçalhos do CSV
    fieldnames = [i[0] for i in cursor.description]

    now = datetime.now()
    now_str = now.strftime('%Y-%m-%d')
    filename = f'{now_str}_lista_de_locacao.csv'

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


@promoter.route('/promoter/error')
def error_page():
    return render_template('promoter/16-error.html')


@promoter.route('/promoter/error-user-not-found')
def error_user_not_found_page():
    return render_template('promoter/17-error-user-not-found.html')


@promoter.route('/promotor')
def redirect_promoter():
    return redirect(url_for('promoter.promoter_scan_start_page'))
