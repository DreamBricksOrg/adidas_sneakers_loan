from flask import Blueprint, request, jsonify, render_template, redirect, url_for, session
from config.database import mysql
from datetime import datetime, timedelta

promoter = Blueprint('promoter', __name__)


@promoter.route('/promoter/start', methods=['GET', 'POST'])
def promoter_scan_start_page():
    if request.method == 'POST':
        estande = request.form['estande']
        session['estande'] = estande
        print(session.get('estande'))
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
        # print(promotor)
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
        return redirect(url_for('promoter.available_shoes_page'))
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM Local")
    locais = cur.fetchall()
    cur.close()
    return render_template('promoter/3-local-confirmation.html', locais=locais)


@promoter.route('/promoter/availableshoes', methods=['GET', 'POST'])
def available_shoes_page():
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

                cur.execute("INSERT INTO LogTenis (Promotor, Local, tamanho, quantidadeOriginal, quantidadeNova, data) VALUES (%s, %s, %s, %s, %s, %s)", (promoter_id, local_id, tenis_id, quantidade_antiga, corrigir, change_date))
                mysql.connection.commit()
        cur.close()
        return redirect(url_for('promoter.promoter_menu_page'))
    else:
        cur = mysql.connection.cursor()
        cur.execute("SELECT id, tamanho, quantidade FROM Tenis WHERE Estande = %s", (session.get('estande'),))
        tenis_disponiveis = cur.fetchall()
        cur.close()
        return render_template('promoter/4-available-shoes.html', tenis_disponiveis=tenis_disponiveis)


@promoter.route('/promoter/ready-start')
def ready_start_page():
    return render_template('promoter/5-ready-start.html')


@promoter.route('/promoter/menu')
def promoter_menu_page():
    if 'logged_in' in session and session['logged_in']:
        return render_template('promoter/6-promoter-menu.html')
    else:
        return redirect(url_for('promoter.promoter_login_page'))


@promoter.route('/promoter/rentallist', methods=['GET', 'POST'])
def rental_list_page():
    if request.method == 'POST':
        return redirect(url_for('promoter.promoter_menu_page'))

    cur = mysql.connection.cursor()
    cur.execute("SELECT Locacao.id,Tenis.tamanho AS Tenis, Usuario.nome_iniciais AS Usuario, Promotor.nome AS "
                "Promotor, Locacao.data_inicio AS Inicio, Locacao.data_fim AS Fim, Locacao.status AS Status, "
                "Local.nome AS Local, Locacao.Estande FROM Locacao JOIN Tenis ON Locacao.Tenis = Tenis.id JOIN Usuario ON "
                "Locacao.Usuario = Usuario.id JOIN Promotor ON Locacao.Promotor = Promotor.id JOIN Local ON "
                "Locacao.Local = Local.id;")
    rentals = cur.fetchall()
    print(rentals)
    cur.close()
    return render_template('promoter/7-rental-list.html', rentals=rentals)


@promoter.route('/promoter/updatevalue', methods=['POST'])
def update_values():
    data = request.json
    tamanho = data.get('tamanho')
    action = data.get('action')

    cur = mysql.connection.cursor()
    cur.execute('SELECT quantidade FROM Tenis WHERE tamanho = %s', (tamanho,))
    # print(tamanho)
    resultado = cur.fetchone()
    # print(resultado)

    if resultado:
        if action == 'increase':
            nova_quantidade = resultado[0] + 1
        elif action == 'decrease':
            nova_quantidade = resultado[0] - 1
        else:
            return "Ação inválida. Use 'increase' ou 'decrease'."
        # print(nova_quantidade)
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
        # print(request.form)
        user_id = request.form['user_id']
        size = request.form['size']
        session['user_id'] = user_id
        session['size'] = size
        return redirect(url_for('promoter.check_user_size_page'))
    return render_template('promoter/8-scan-aprove-rental.html')


@promoter.route('/promoter/checkuser', methods=['GET'])
def check_user_size_page():
    user_id = session['user_id']
    size = session['size']

    cur = mysql.connection.cursor()
    cur.execute("SELECT Usuario.nome_iniciais "
                "FROM Usuario "
                "WHERE Usuario.id = %s;", (user_id,))
    result = cur.fetchone()
    cur.close()

    if not result:
        cur.close()
        return jsonify({'message': 'user not found'}), 404

    now = datetime.now()
    start_date = now.strftime('%Y-%m-%d %H:%M:%S')

    return render_template('promoter/15-check-user.html', user_name=result[0], size=size, start_date=start_date)


@promoter.route('/promoter/captureid', methods=['GET', 'POST'])
def capture_id():
    if request.method == 'POST':
        files = request.files
        file = files.get('file')
        print(file)

        user_id = session['user_id']
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO Fotos (Usuario, documento) VALUES(%s, %s)", (user_id, file.read(),))
        mysql.connection.commit()
        cur.close()

        return redirect(url_for('promoter.capture_portrait'))

    return render_template('promoter/13-capture-id.html')


@promoter.route('/promoter/captureportrait', methods=['GET', 'POST'])
def capture_portrait():
    if request.method == 'POST':
        files = request.files
        file = files.get('file')
        print(file)

        user_id = session['user_id']

        cur = mysql.connection.cursor()
        # cur.execute("INSERT INTO Fotos (Usuario, documento, retrato) VALUES(%s)", (user_id, id_file.read(), file.read(),))
        cur.execute("UPDATE Fotos SET retrato = %s WHERE Usuario = %s", (file.read(), user_id,))
        mysql.connection.commit()
        cur.close()

        return redirect(url_for('promoter.aprove_rental_page'))

    return render_template('promoter/14-capture-portrait.html')


@promoter.route('/promoter/aproverental', methods=['GET', 'POST'])
def aprove_rental_page():
    cur = mysql.connection.cursor()

    size = session.get('size')

    user_id = session.get('user_id')

    promoter_id = session.get('promoter_id')

    local_id = session.get('local_id')
    cur.execute('SELECT nome FROM Local WHERE id = %s', (local_id,))
    local = cur.fetchone()

    estande = session.get('estande')

    now = datetime.now()
    data_inicio = now.strftime('%Y-%m-%d %H:%M:%S')

    future_time = now + timedelta(minutes=45)
    data_fim = future_time.strftime('%Y-%m-%d %H:%M:%S')

    status = 'ALOCADO'

    cur.execute('SELECT id FROM Tenis WHERE tamanho = %s AND estande = %s', (size, estande))
    tenis_id = cur.fetchone()

    if request.method == 'POST':
        cur.execute('SELECT Usuario FROM Locacao WHERE Usuario = %s', (user_id,))
        result = cur.fetchone()

        if result:
            return redirect(url_for('promoter.rental_list_page'))
        else:
            cur.execute(
                'INSERT INTO Locacao (Tenis, Usuario, Promotor, Local, Estande, data_inicio, data_fim, status) VALUES ( %s, %s, %s, %s, %s, %s, %s, %s)',
                (tenis_id[0], user_id, promoter_id, local_id[0], estande, data_inicio, data_fim, status))
            mysql.connection.commit()

            if cur.lastrowid != 0:
                cur.execute('SELECT quantidade FROM Tenis WHERE tamanho = %s', (size,))
                quantidade = cur.fetchone()
                nova_quantidade = quantidade[0] - 1
                cur.execute('UPDATE Tenis SET quantidade = %s WHERE tamanho = %s', (nova_quantidade, size))
                mysql.connection.commit()

                cur.execute('SELECT id FROM Usuario WHERE id = %s', (user_id,))
                user = cur.fetchone()
                if user:
                    cur.execute('UPDATE Usuario SET aprovado = true WHERE id = %s', (user_id,))
                    mysql.connection.commit()

                    cur.execute('UPDATE Usuario SET local_de_locacao = %s WHERE id = %s', (local[0], user_id))
                    mysql.connection.commit()

                cur.close()
            return redirect(url_for('promoter.rental_list_page'))

    cur.execute("SELECT nome_iniciais FROM Usuario WHERE id = %s ", (user_id,))
    user_name = cur.fetchone()
    cur.close()
    return render_template('promoter/9-aprove-rental.html', user_name=user_name[0], start_date=data_inicio, size=size)


@promoter.route('/promoter/scanreturn', methods=['GET', 'POST'])
def scan_return_page():
    if request.method == 'POST':
        user_id = request.form['user_id']
        size = request.form['size']
        session['user_id'] = user_id
        session['size'] = size

        return redirect(url_for('promoter.return_page'))
    return render_template('promoter/10-scan-return.html')


@promoter.route('/promoter/return', methods=['GET', 'POST'])
def return_page():
    user_id = session.get('user_id')
    size = session.get('size')

    cur = mysql.connection.cursor()
    cur.execute("SELECT U.nome_iniciais, L.Tenis, L.data_inicio, L.status "
                "FROM Usuario U, Locacao L "
                "WHERE U.id = L.Usuario "
                "AND U.id = %s;", (user_id,))

    locacao = cur.fetchone()

    if request.method == 'POST':
        if locacao[3] == 'ALOCADO' or locacao[3] == 'VENCIDO':

            cur.execute('SELECT quantidade FROM Tenis WHERE tamanho = %s', (size,))
            quantidade = cur.fetchone()

            nova_quantidade = quantidade[0] + 1
            cur.execute('UPDATE Tenis SET quantidade = %s WHERE tamanho = %s', (nova_quantidade, size))
            mysql.connection.commit()

            cur.execute("UPDATE Locacao SET status = 'DEVOLVIDO' WHERE Usuario = %s", (user_id,))
            mysql.connection.commit()

            cur.execute('SELECT id FROM Usuario WHERE id = %s', (user_id,))
            user = cur.fetchone()
            print(user)
            if user:
                cur.execute('UPDATE Usuario SET retornado = true WHERE id = %s', (user_id,))
                mysql.connection.commit()

        cur.close()
        return redirect(url_for('promoter.promoter_menu_page'))

    cur.close()

    if not locacao:
        cur.close()
        return jsonify({'message': 'user not found'}), 404

    end_date = datetime.now()
    start_date = locacao[2]
    duration = end_date - start_date
    duration_minutes = int(duration.total_seconds() / 60)

    return render_template('promoter/11-return.html', user_name=locacao[0], size=size, start_date=start_date,
                           duration=duration_minutes)

@promoter.route('/promoter/returnwithproblems', methods=['GET', 'POST'])
def return_with_problems_page():
    user_id = session.get('user_id')
    size = session.get('size')

    cur = mysql.connection.cursor()
    cur.execute("SELECT U.nome_iniciais, L.Tenis, L.data_inicio, L.status "
                "FROM Usuario U, Locacao L "
                "WHERE U.id = L.Usuario "
                "AND U.id = %s;", (user_id,))

    locacao = cur.fetchone()

    if request.method == 'POST':
        if locacao[3] == 'ALOCADO' or locacao[3] == 'VENCIDO':

            cur.execute("UPDATE Locacao SET status = 'DEVOLVIDO' WHERE Usuario = %s", (user_id,))
            mysql.connection.commit()

            cur.execute('SELECT id FROM Usuario WHERE id = %s', (user_id,))
            user = cur.fetchone()
            print(user)
            if user:
                cur.execute('UPDATE Usuario SET retornado = true WHERE id = %s', (user_id,))
                mysql.connection.commit()

        cur.close()
        return redirect(url_for('promoter.promoter_menu_page'))

    cur.close()

    if not locacao:
        cur.close()
        return jsonify({'message': 'user not found'}), 404

    end_date = datetime.now()
    start_date = locacao[2]
    duration = end_date - start_date
    duration_minutes = int(duration.total_seconds() / 60)

    return render_template('promoter/11-return.html', user_name=locacao[0], size=size, start_date=start_date,
                           duration=duration_minutes)


@promoter.route('/promoter/rentallistexpired', methods=['GET', 'POST'])
def rental_list_expired_page():
    if request.method == 'POST':
        session.clear()
        return redirect(url_for('promoter.promoter_menu_page'))

    cur = mysql.connection.cursor()
    cur.execute("SELECT Locacao.id,Tenis.tamanho AS Tenis, Usuario.nome_iniciais AS Usuario, Promotor.nome AS "
                "Promotor, Locacao.data_inicio AS Inicio, Locacao.data_fim AS Fim, Locacao.status AS Status, "
                "Local.nome AS Local, Locacao.Estande FROM Locacao JOIN Tenis ON Locacao.Tenis = Tenis.id JOIN Usuario ON "
                "Locacao.Usuario = Usuario.id JOIN Promotor ON Locacao.Promotor = Promotor.id JOIN Local ON "
                "Locacao.Local = Local.id WHERE Locacao.status = 'VENCIDO';")
    rentals = cur.fetchall()
    cur.close()
    return render_template('promoter/12-expired-list.html', rentals=rentals)
