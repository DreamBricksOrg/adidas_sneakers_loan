from flask import Blueprint, request, jsonify, render_template, redirect, url_for, session, make_response
from database import mysql

promoter = Blueprint('promoter', __name__)


@promoter.route('/promoter/login')
def promoter_login_page():
    return render_template('promoter/2-promoter-login.html')


@promoter.route('/promoter/local', methods=['GET', 'POST'])
def promoter_local_page():
    if request.method == 'POST':
        local = request.form['local']
        session['local'] = local
        session['estande'] = '1'
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


@promoter.route('/promoter/scaraproverental', methods=['GET', 'POST'])
def scan_aprove_rental_page():
    return render_template('8-scan-aprove-rental.html')


@promoter.route('/promoter/aproverental', methods=['GET', 'POST'])
def aprove_rental_page():
    return render_template('promoter/9-aprove-rental.html')


@promoter.route('/promoter/scanreturn', methods=['GET', 'POST'])
def scan_return_page():
    return render_template('promoter/10-scan-return.html')


@promoter.route('/promoter/return', methods=['GET', 'POST'])
def return_page():
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
