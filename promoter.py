from flask import Blueprint, request, jsonify, render_template, redirect, url_for, session, make_response
from database import mysql

promoter = Blueprint('promoter', __name__)


@promoter.route('/promoter/start', methods=['GET', 'POST'])
def promoter_scan_start_page():
    if request.method == 'POST':
        estande = request.form['estande']
        session['estande'] = estande
        return redirect(url_for('promoter.promoter_login_page'))

    return render_template('promoter/1-scan-start.html')


@promoter.route('/promoter/login')
def promoter_login_page():
    return render_template('promoter/2-promoter-login.html')


@promoter.route('/promoter/local', methods=['GET', 'POST'])
def promoter_local_page():
    if request.method == 'POST':
        local = request.form['local']
        session['local'] = local
        return redirect(url_for('promoter.available_shoes_page'))
    cur = mysql.connection.cursor()
    cur.execute("SELECT nome FROM Local")
    locais = cur.fetchall()
    cur.close()
    return render_template('promoter/3-local-confirmation.html', locais=locais)


@promoter.route('/promoter/availableshoes', methods=['GET', 'POST'])
def available_shoes_page():
    if request.method == 'POST':
        cur = mysql.connection.cursor()
        for i in range(1, len(request.form) // 3 + 1):
            corrigir = request.form.get(f'corrigir_quantidade_{i}', '').strip()
            tenis_id = request.form.get(f'tenis_id_{i}')
            if corrigir:
                cur.execute("UPDATE Tenis SET quantidade = %s WHERE id = %s", (corrigir, tenis_id))
            mysql.connection.commit()
        cur.close()
        return redirect(url_for('promoter.ready_start_page'))
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
    return render_template('promoter/6-promoter-menu.html')


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
    cur.close()
    return render_template('promoter/7-rental-list.html', rentals=rentals)


@promoter.route('/promoter/updatevalue', methods=['POST'])
def update_values():
    data = request.json
    tamanho = data.get('tamanho')
    action = data.get('action')

    cur = mysql.connection.cursor()
    cur.execute('SELECT quantidade FROM Tenis WHERE tamanho = %s', (tamanho,))
    print(tamanho)
    resultado = cur.fetchone()
    print(resultado)

    if resultado:
        if action == 'increase':
            nova_quantidade = resultado[0] + 1
        elif action == 'decrease':
            nova_quantidade = resultado[0] - 1
        else:
            return "Ação inválida. Use 'increase' ou 'decrease'."
        print(nova_quantidade)
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
    cur.execute('UPDATE Locacao SET Tenis = %s WHERE Tenis = %s', (new_tennis_id[0], old_tennis_id[0]))
    mysql.connection.commit()

    cur.close()
    return jsonify({'message': 'Locacao updated successfully'}), 200


@promoter.route('/promoter/scanaproverental', methods=['GET', 'POST'])
def scan_aprove_rental_page():
    if request.method == 'POST':
        user_id = request.form['user_id']
        size = request.form['size']
        session['user_id'] = user_id
        session['size'] = size
        return redirect(url_for('promoter.aprove_rental_page'))
    return render_template('promoter/8-scan-aprove-rental.html')


@promoter.route('/promoter/aproverental', methods=['GET', 'POST'])
def aprove_rental_page():
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

    return render_template('promoter/9-aprove-rental.html', name=result[0], size=size)


@promoter.route('/promoter/scanreturn', methods=['GET', 'POST'])
def scan_return_page():
    if request.method == 'POST':
        user_id = request.form['user_id']
        session['user_id'] = user_id

        return redirect(url_for('promoter.return_page'))
    return render_template('promoter/10-scan-return.html')


@promoter.route('/promoter/return', methods=['GET', 'POST'])
def return_page():
    # user_id
    return render_template('promoter/11-return.html')


@promoter.route('/promoter/rentallistexpired', methods=['GET', 'POST'])
def rental_list_expired_page():
    if request.method == 'POST':
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
