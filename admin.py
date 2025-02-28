import csv
import base64
from datetime import datetime, timedelta
from fileinput import filename

from flask import Blueprint, request, session, redirect, url_for, render_template, make_response, send_file, jsonify

from config.database import mysql
import json
import pandas as pd
from io import BytesIO

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

@admin.route('/admin/menu/admin')
def admin_menu_admin_page():
    if 'logged_in' in session and session['logged_in']:
        return render_template('admin/7-admin-menu-admin.html')
    else:
        return redirect(url_for('admin.admin_login_page'))


@admin.route('/admin/stock')
def stock_page():
    if 'logged_in' in session and session['logged_in']:
        return render_template('promoter/4-available-shoes.html')
    else:
        return redirect(url_for('admin.admin_login_page'))

@admin.route('/admin/dashboard')
def dashboard_page():
    if 'logged_in' in session and session['logged_in']:
        return render_template('admin/8-dashboard.html')
    else:
        return redirect(url_for('admin.admin_login_page'))

@admin.route('/admin/querys')
def query_page():
    if 'logged_in' in session and session['logged_in']:
        return render_template('admin/9-querys.html')
    else:
        return redirect(url_for('admin.admin_login_page'))


@admin.route('/admin/get_data_models_per_day', methods=['GET', 'POST'])
def get_data_models_per_day():
    cur = mysql.connection.cursor()

    cur.execute("SET SESSION group_concat_max_len = 10000;")

    cur.execute("""
        SELECT GROUP_CONCAT(
            CONCAT(
                'SUM(CASE WHEN Modelo.nome = "', nome, '" THEN 1 ELSE 0 END) AS `', REPLACE(nome, '`', ''), '`'
            )
        ) 
        FROM Modelo
    """)

    colunas_sum_case = cur.fetchone()[0]

    if not colunas_sum_case:
        colunas_sum_case = "0 AS `No Data`"

    ano = request.args.get('ano', type=int)

    sql = f"""
        SELECT 
            DATE_FORMAT(Locacao.data_inicio, "%y-%m-%d") AS bdate, 
            Veiculo.nome AS nome_veiculo, 
            {colunas_sum_case}, 
            COUNT(1) AS num
        FROM 
            Locacao
        JOIN 
            Veiculo ON Locacao.Veiculo = Veiculo.id
        JOIN 
            Tenis ON Locacao.Tenis = Tenis.id
        JOIN 
            Modelo ON Tenis.Modelo = Modelo.id
        WHERE 
            {f"YEAR(Locacao.data_inicio) = {ano}" if ano else "1=1"}
        GROUP BY 
            DATE_FORMAT(Locacao.data_inicio, "%y-%m-%d"), Veiculo.nome
        ORDER BY 
            DATE_FORMAT(Locacao.data_inicio, "%y-%m-%d") DESC, Veiculo.nome DESC;
    """

    return jsonify(fetch_data(sql))


@admin.route('/admin/get_data_status_per_day', methods=['GET', 'POST'])
def get_data_status_per_day():
    ano = request.args.get('ano', type=int)

    sql = f"""
        SELECT 
            DATE_FORMAT(Locacao.data_inicio, "%y-%m-%d") AS bdate, 
            Veiculo.nome AS nome_veiculo,
            SUM(CASE WHEN Locacao.status = 'DEVOLVIDO' THEN 1 ELSE 0 END) AS 'DEVOLVIDO',
            SUM(CASE WHEN Locacao.status = 'CANCELADO' THEN 1 ELSE 0 END) AS 'CANCELADO',
            SUM(CASE WHEN Locacao.status = 'VENCIDO' THEN 1 ELSE 0 END) AS 'VENCIDO',
            COUNT(1) AS num
        FROM 
            Locacao
        JOIN 
            Veiculo ON Locacao.Veiculo = Veiculo.id
        WHERE 
            {f"YEAR(Locacao.data_inicio) = {ano}" if ano else "1=1"}
        GROUP BY 
            DATE_FORMAT(Locacao.data_inicio, "%y-%m-%d"), Veiculo.nome
        ORDER BY 
            DATE_FORMAT(Locacao.data_inicio, "%y-%m-%d") DESC, Veiculo.nome DESC;
    """

    return jsonify(fetch_data(sql))


@admin.route('/admin/get_data_gen_per_day', methods=['GET', 'POST'])
def get_data_gen_per_day():
    ano = request.args.get('ano', type=int)

    sql = f"""
        SELECT 
            DATE_FORMAT(Locacao.data_inicio, "%y-%m-%d") AS bdate, 
            Veiculo.nome AS nome_veiculo,
            SUM(CASE WHEN SUBSTRING(Tenis.tamanho, 1, 1) = 'M' THEN 1 ELSE 0 END) AS Masculino,
            SUM(CASE WHEN SUBSTRING(Tenis.tamanho, 1, 1) = 'F' THEN 1 ELSE 0 END) AS Feminino,
            SUM(CASE WHEN SUBSTRING(Tenis.tamanho, 1, 1) = 'U' THEN 1 ELSE 0 END) AS Unissex,
            COUNT(1) AS total
        FROM 
            Locacao
        JOIN 
            Veiculo ON Locacao.Veiculo = Veiculo.id
        JOIN 
            Tenis ON Locacao.Tenis = Tenis.id
        WHERE 
            {f"YEAR(Locacao.data_inicio) = {ano}" if ano else "1=1"}
        GROUP BY 
            DATE_FORMAT(Locacao.data_inicio, "%y-%m-%d"), Veiculo.nome
        ORDER BY 
            DATE_FORMAT(Locacao.data_inicio, "%y-%m-%d") DESC, Veiculo.nome DESC;
    """

    return jsonify(fetch_data(sql))


@admin.route('/admin/get_data_num_per_day', methods=['GET', 'POST'])
def get_data_num_per_day():
    ano = request.args.get('ano', type=int)

    sql = f"""
        SELECT 
            DATE_FORMAT(Locacao.data_inicio, "%y-%m-%d") AS bdate, 
            Veiculo.nome AS nome_veiculo,
            SUM(CASE WHEN CAST(SUBSTRING(Tenis.tamanho, 2) AS UNSIGNED) = 34 THEN 1 ELSE 0 END) AS Tamanho_34,
            SUM(CASE WHEN CAST(SUBSTRING(Tenis.tamanho, 2) AS UNSIGNED) = 35 THEN 1 ELSE 0 END) AS Tamanho_35,
            SUM(CASE WHEN CAST(SUBSTRING(Tenis.tamanho, 2) AS UNSIGNED) = 36 THEN 1 ELSE 0 END) AS Tamanho_36,
            SUM(CASE WHEN CAST(SUBSTRING(Tenis.tamanho, 2) AS UNSIGNED) = 37 THEN 1 ELSE 0 END) AS Tamanho_37,
            SUM(CASE WHEN CAST(SUBSTRING(Tenis.tamanho, 2) AS UNSIGNED) = 38 THEN 1 ELSE 0 END) AS Tamanho_38,
            SUM(CASE WHEN CAST(SUBSTRING(Tenis.tamanho, 2) AS UNSIGNED) = 39 THEN 1 ELSE 0 END) AS Tamanho_39,
            SUM(CASE WHEN CAST(SUBSTRING(Tenis.tamanho, 2) AS UNSIGNED) = 40 THEN 1 ELSE 0 END) AS Tamanho_40,
            SUM(CASE WHEN CAST(SUBSTRING(Tenis.tamanho, 2) AS UNSIGNED) = 41 THEN 1 ELSE 0 END) AS Tamanho_41,
            SUM(CASE WHEN CAST(SUBSTRING(Tenis.tamanho, 2) AS UNSIGNED) = 42 THEN 1 ELSE 0 END) AS Tamanho_42,
            SUM(CASE WHEN CAST(SUBSTRING(Tenis.tamanho, 2) AS UNSIGNED) = 43 THEN 1 ELSE 0 END) AS Tamanho_43,
            SUM(CASE WHEN CAST(SUBSTRING(Tenis.tamanho, 2) AS UNSIGNED) = 44 THEN 1 ELSE 0 END) AS Tamanho_44,
            SUM(CASE WHEN CAST(SUBSTRING(Tenis.tamanho, 2) AS UNSIGNED) = 45 THEN 1 ELSE 0 END) AS Tamanho_45,
            COUNT(1) AS total
        FROM 
            Locacao
        JOIN 
            Veiculo ON Locacao.Veiculo = Veiculo.id
        JOIN 
            Tenis ON Locacao.Tenis = Tenis.id
        WHERE 
            {f"YEAR(Locacao.data_inicio) = {ano}" if ano else "1=1"}
        GROUP BY 
            DATE_FORMAT(Locacao.data_inicio, "%y-%m-%d"), Veiculo.nome
        ORDER BY 
            DATE_FORMAT(Locacao.data_inicio, "%y-%m-%d") DESC, Veiculo.nome DESC;
    """

    return jsonify(fetch_data(sql))


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
        """ 
        SELECT 
    Promotor.nome AS Promotor, 
    Veiculo.nome AS Veiculo, 
    Modelo.nome AS Modelo,
    Tenis.tamanho AS Tamanho, 
    quantidadeOriginal, 
    quantidadeNova, 
    data 
FROM 
    LogTenis 
JOIN 
    Promotor ON LogTenis.Promotor = Promotor.id 
JOIN 
    Tenis ON LogTenis.Tenis = Tenis.id 
JOIN 
    Veiculo ON LogTenis.Veiculo = Veiculo.id
JOIN 
    Modelo ON Tenis.Modelo = Modelo.id;       
        """)

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
    cursor.execute("""
        SELECT Usuario.id,
           Usuario.dados_criptografados,
           Modelo.nome AS Modelo,
           Tenis.tamanho AS Tamnho,
           Locacao.data_inicio AS Inicio,
           Locacao.data_fim AS Fim,
           Usuario.confirmacao_sms,
           Locacao.status AS Status,
           Promotor.nome AS promotor,
           Locacao.Estande,
           Veiculo.nome AS Veiculo
    FROM Locacao
    JOIN Tenis ON Locacao.Tenis = Tenis.id
    JOIN Modelo ON Tenis.Modelo = Modelo.id
    JOIN Usuario ON Locacao.Usuario = Usuario.id
    JOIN Promotor ON Locacao.Promotor = Promotor.id
    JOIN Veiculo ON Locacao.Veiculo = Veiculo.id
    ORDER BY Locacao.data_inicio DESC;
    """)

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


@admin.route('/create_sneaker_model', methods=['POST'])
def create_sneaker_model():
    data = request.json
    modelo_name = data.get("modelo_name")
    estande_name = data.get("estande")

    if not modelo_name or not estande_name:
        return jsonify({"error": "Os campos 'modelo_name' e 'estande' são obrigatórios"}), 400

    try:
        cur = mysql.connection.cursor()

        # Criar o novo modelo na tabela Modelo
        cur.execute("INSERT INTO Modelo (nome, status) VALUES (%s, 'ATIVO')", (modelo_name,))
        mysql.connection.commit()
        modelo_id = cur.lastrowid  # Pega o ID do modelo recém-criado

        # Buscar o ID do Estande pelo nome
        cur.execute("SELECT id FROM Estande WHERE nome = %s", (estande_name,))
        estande_result = cur.fetchone()
        if not estande_result:
            return jsonify({"error": "Estande não encontrado"}), 404
        estande_id = estande_result[0]  # Acessando a primeira posição da tupla corretamente

        # Gerar os tamanhos
        tamanhos = []
        for prefixo in ["F", "M", "U"]:
            for num in range(34, 46):
                tamanhos.append(f"{prefixo}{num}")

        # Inserir os tênis na tabela Tenis
        for tamanho in tamanhos:
            cur.execute("INSERT INTO Tenis (tamanho, quantidade, Estande, Modelo) VALUES (%s, 0, %s, %s)",
                        (tamanho, estande_id, modelo_id))

        mysql.connection.commit()

        return jsonify(
            {"message": "Modelo e Tênis criados com sucesso", "modelo_id": modelo_id, "estande_id": estande_id})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        cur.close()


def fetch_data(query):
    cur = mysql.connection.cursor()
    cur.execute(query)
    rows = cur.fetchall()

    column_names = [desc[0] for desc in cur.description]

    data = [dict(zip(column_names, row)) for row in rows]

    cur.close()
    return {"columns": column_names, "data": data}


@admin.route("/admin/get_data_weekday", methods=["GET"])
def get_data_by_weekday():
    ano = request.args.get("ano", type=int)
    query = f"""
        SELECT 
            CASE T.wd
                WHEN 'Sunday' THEN 'Domingo'
                WHEN 'Monday' THEN 'Segunda'
                WHEN 'Tuesday' THEN 'Terça'
                WHEN 'Wednesday' THEN 'Quarta'
                WHEN 'Thursday' THEN 'Quinta'
                WHEN 'Friday' THEN 'Sexta'
                WHEN 'Saturday' THEN 'Sábado'
            END AS dia_semana,
            T.num
        FROM (
            SELECT weekday(data_inicio) AS id, 
                   dayname(data_inicio) AS wd, 
                   count(id) AS num
            FROM Locacao
            WHERE {f"YEAR(data_inicio) = {ano}" if ano else "1=1"}
            GROUP BY weekday(data_inicio), dayname(data_inicio)
            ORDER BY id
        ) AS T;
    """
    return jsonify(fetch_data(query))


@admin.route("/admin/get_data_vehicle", methods=["GET"])
def get_data_by_vehicle():
    ano = request.args.get("ano", type=int)
    query = f"""
        SELECT 
            V.nome AS Veiculo,
            COUNT(1) AS num
        FROM Locacao L
        JOIN Veiculo V ON L.Veiculo = V.id
        WHERE {f"YEAR(L.data_inicio) = {ano}" if ano else "1=1"}
        GROUP BY Veiculo
        ORDER BY Veiculo;
    """
    return jsonify(fetch_data(query))


@admin.route("/admin/get_data_tipo_treino", methods=["GET"])
def get_data_by_tipo_treino():
    ano = request.args.get("ano", type=int)
    query = f"""
        SELECT IFNULL(TT.nome, 'ND') AS TipoTreino, COUNT(1) AS num
        FROM Locacao L
        LEFT JOIN TipoTreino TT ON L.TipoTreino = TT.id
        WHERE {f"YEAR(L.data_inicio) = {ano}" if ano else "1=1"}
        GROUP BY TipoTreino
        ORDER BY TipoTreino;
    """
    return jsonify(fetch_data(query))


@admin.route("/admin/get_data_local", methods=["GET"])
def get_data_by_local():
    ano = request.args.get("ano", type=int)
    query = f"""
        SELECT 
            IFNULL(Loc.cidade, 'ND') AS cidade,
            IFNULL(Loc.estado, 'ND') AS estado,
            count(1) AS num
        FROM Locacao L
        LEFT JOIN Local Loc ON L.Local = Loc.id
        WHERE {f"YEAR(L.data_inicio) = {ano}" if ano else "1=1"}
        GROUP BY cidade, estado;
    """
    return jsonify(fetch_data(query))


@admin.route("/admin/get_data_local_treino", methods=["GET"])
def get_data_by_local_treino():
    ano = request.args.get("ano", type=int)
    query = f"""
        SELECT IFNULL(LT.nome, 'ND') AS LocalTreino, COUNT(1) AS num
        FROM Locacao L
        LEFT JOIN LocalTreino LT ON L.LocalTreino = LT.id
        WHERE {f"YEAR(L.data_inicio) = {ano}" if ano else "1=1"}
        GROUP BY LocalTreino
        ORDER BY LocalTreino;
    """
    return jsonify(fetch_data(query))


@admin.route("/admin/get_data_franquia", methods=["GET"])
def get_data_by_franquia():
    ano = request.args.get("ano", type=int)
    query = f"""
        SELECT M.nome AS Franquia, COUNT(1) AS num
        FROM Locacao L
        JOIN Tenis T ON L.Tenis = T.id
        JOIN Modelo M ON T.Modelo = M.id
        WHERE {f"YEAR(L.data_inicio) = {ano}" if ano else "1=1"}
        GROUP BY Franquia
        ORDER BY Franquia;
    """
    return jsonify(fetch_data(query))


@admin.route("/admin/get_data_day", methods=["GET"])
def get_data_by_day():
    ano = request.args.get("ano", type=int)
    query = f"""
        SELECT DATE_FORMAT(data_inicio, '%d-%m-%Y') as dia, count(1) as num
        FROM Locacao
        WHERE {f"YEAR(data_inicio) = {ano}" if ano else "1=1"}
        GROUP BY DATE_FORMAT(data_inicio, '%Y%m%d'), DATE_FORMAT(data_inicio, '%d-%m-%Y')
        ORDER BY DATE_FORMAT(data_inicio, '%Y%m%d');
    """
    return jsonify(fetch_data(query))


@admin.route("/admin/get_data_day_period", methods=["GET"])
def get_data_by_day_period():
    ano = request.args.get("ano", type=int)
    query = f"""
        SELECT 
            CASE
                WHEN HOUR(data_inicio) >= 6 AND HOUR(data_inicio) < 12 THEN '0 Dia (6h-12h)'
                WHEN HOUR(data_inicio) >= 12 AND HOUR(data_inicio) < 18 THEN '1 Tarde (12h-18h)'
                ELSE '2 Noite (18h-6h)'
            END AS period,
            COUNT(1) AS num
        FROM Locacao
        WHERE {f"YEAR(data_inicio) = {ano}" if ano else "1=1"}
        GROUP BY period
        ORDER BY period;
    """
    return jsonify(fetch_data(query))


@admin.route("/admin/get_data_all", methods=["GET"])
def get_data_all():
    ano = request.args.get("ano", type=int)
    query = f"""
        SELECT 
            L.data_inicio, 
            IFNULL(L.data_fim, '2000-01-01 00:00:00') AS data_fim, 
            L.status, 
            T.Modelo AS Tenis, 
            T.tamanho,
            U.nome_iniciais AS Usuario, 
            U.documento, 
            IFNULL(U.veiculo_de_locacao, 'ND') AS veiculo_de_locacao,
            U.confirmacao_sms, 
            IFNULL(U.aprovado, 0) AS aprovado,
            IFNULL(U.retornado, 0) AS retornado, 
            U.data_registro,
            P.nome AS Promotor, 
            P.usuario AS PromotorUser,
            V.nome AS Veiculo,
            E.nome AS Estande,
            IFNULL(Loc.cidade, 'ND') AS cidade,
            IFNULL(Loc.estado, 'ND') AS estado,
            IFNULL(LT.nome, 'ND') AS LocalTreino,
            IFNULL(TT.nome, 'ND') AS TipoTreino
        FROM Locacao L
        JOIN Tenis T ON L.Tenis = T.id
        JOIN Usuario U ON L.Usuario = U.id
        JOIN Promotor P ON L.Promotor = P.id
        JOIN Veiculo V ON L.Veiculo = V.id
        JOIN Estande E ON L.Estande = E.id
        LEFT JOIN Local Loc ON L.Local = Loc.id
        LEFT JOIN LocalTreino LT ON L.LocalTreino = LT.id
        LEFT JOIN TipoTreino TT ON L.TipoTreino = TT.id
        WHERE {f"YEAR(L.data_inicio) = {ano}" if ano else "1=1"};
    """
    return jsonify(fetch_data(query))


@admin.route('/admin/get_data_status')
def get_data_status():
    try:
        query = """
            SELECT 
                Veiculo.nome AS nome_veiculo,
                SUM(CASE WHEN Locacao.status = 'DEVOLVIDO' THEN 1 ELSE 0 END) AS DEVOLVIDO,
                SUM(CASE WHEN Locacao.status = 'CANCELADO' THEN 1 ELSE 0 END) AS CANCELADO,
                SUM(CASE WHEN Locacao.status = 'VENCIDO' THEN 1 ELSE 0 END) AS VENCIDO,
                COUNT(1) AS total
            FROM Locacao
            JOIN Veiculo ON Locacao.Veiculo = Veiculo.id
            GROUP BY nome_veiculo
            ORDER BY nome_veiculo;
        """

        cur = mysql.connection.cursor()
        cur.execute(query)
        rows = cur.fetchall()
        columns = [desc[0] for desc in cur.description]

        # Formatar resultado como JSON
        result = [dict(zip(columns, row)) for row in rows]

        cur.close()
        return jsonify({"columns": columns, "data": result})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@admin.route('/admin/get_data_gen')
def get_data_gen():
    try:
        query = """
            SELECT 
                SUM(CASE WHEN SUBSTRING(Tenis.tamanho, 1, 1) = 'M' THEN 1 ELSE 0 END) AS Masculino,
                SUM(CASE WHEN SUBSTRING(Tenis.tamanho, 1, 1) = 'F' THEN 1 ELSE 0 END) AS Feminino,
                SUM(CASE WHEN SUBSTRING(Tenis.tamanho, 1, 1) = 'U' THEN 1 ELSE 0 END) AS Unissex
            FROM Locacao
            JOIN Tenis ON Locacao.Tenis = Tenis.id;
        """

        cur = mysql.connection.cursor()
        cur.execute(query)
        row = cur.fetchone()
        cur.close()

        # Estrutura de resposta no formato JSON
        data = [
            {"Genero": "Masculino", "Quantidade": row[0]},
            {"Genero": "Feminino", "Quantidade": row[1]},
            {"Genero": "Unissex", "Quantidade": row[2]}
        ]

        return jsonify({"columns": ["Genero", "Quantidade"], "data": data})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Endpoint para dados de tamanho
@admin.route('/admin/get_data_tam')
def get_data_tam():
    try:
        query = """
            SELECT 
                DATE_FORMAT(Locacao.data_inicio, "%y-%m-%d") AS bdate, 
                Veiculo.nome AS nome_veiculo,
                SUM(CASE WHEN CAST(SUBSTRING(Tenis.tamanho, 2) AS UNSIGNED) = 34 THEN 1 ELSE 0 END) AS Tamanho_34,
                SUM(CASE WHEN CAST(SUBSTRING(Tenis.tamanho, 2) AS UNSIGNED) = 35 THEN 1 ELSE 0 END) AS Tamanho_35,
                SUM(CASE WHEN CAST(SUBSTRING(Tenis.tamanho, 2) AS UNSIGNED) = 36 THEN 1 ELSE 0 END) AS Tamanho_36,
                SUM(CASE WHEN CAST(SUBSTRING(Tenis.tamanho, 2) AS UNSIGNED) = 37 THEN 1 ELSE 0 END) AS Tamanho_37,
                SUM(CASE WHEN CAST(SUBSTRING(Tenis.tamanho, 2) AS UNSIGNED) = 38 THEN 1 ELSE 0 END) AS Tamanho_38,
                SUM(CASE WHEN CAST(SUBSTRING(Tenis.tamanho, 2) AS UNSIGNED) = 39 THEN 1 ELSE 0 END) AS Tamanho_39,
                SUM(CASE WHEN CAST(SUBSTRING(Tenis.tamanho, 2) AS UNSIGNED) = 40 THEN 1 ELSE 0 END) AS Tamanho_40,
                SUM(CASE WHEN CAST(SUBSTRING(Tenis.tamanho, 2) AS UNSIGNED) = 41 THEN 1 ELSE 0 END) AS Tamanho_41,
                SUM(CASE WHEN CAST(SUBSTRING(Tenis.tamanho, 2) AS UNSIGNED) = 42 THEN 1 ELSE 0 END) AS Tamanho_42,
                SUM(CASE WHEN CAST(SUBSTRING(Tenis.tamanho, 2) AS UNSIGNED) = 43 THEN 1 ELSE 0 END) AS Tamanho_43,
                SUM(CASE WHEN CAST(SUBSTRING(Tenis.tamanho, 2) AS UNSIGNED) = 44 THEN 1 ELSE 0 END) AS Tamanho_44,
                SUM(CASE WHEN CAST(SUBSTRING(Tenis.tamanho, 2) AS UNSIGNED) = 45 THEN 1 ELSE 0 END) AS Tamanho_45
            FROM Locacao
            JOIN Veiculo ON Locacao.Veiculo = Veiculo.id
            JOIN Tenis ON Locacao.Tenis = Tenis.id
            GROUP BY bdate, nome_veiculo
            ORDER BY bdate;
        """

        cur = mysql.connection.cursor()
        cur.execute(query)
        rows = cur.fetchall()
        columns = [desc[0] for desc in cur.description]
        cur.close()

        # Formatar a resposta em JSON
        data = [dict(zip(columns, row)) for row in rows]

        return jsonify({"columns": columns, "data": data})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@admin.route('/admin/get_data_modelo')
def get_data_modelo():
    try:
        cur = mysql.connection.cursor()

        # Obter todos os nomes de modelos para gerar colunas dinamicamente
        cur.execute("SELECT nome FROM Modelo")
        modelos = [row[0] for row in cur.fetchall()]

        if not modelos:
            return jsonify({"error": "Nenhum modelo encontrado"}), 404

        # Gerar as colunas SUM(CASE...)
        colunas_sum_case = ", ".join(
            [f"SUM(CASE WHEN Modelo.nome = '{modelo}' THEN 1 ELSE 0 END) AS `{modelo}`" for modelo in modelos]
        )

        # Query final com contagem por modelo
        query = f"""
            SELECT 
                DATE_FORMAT(Locacao.data_inicio, "%y-%m-%d") AS bdate,
                Veiculo.nome AS nome_veiculo,
                {colunas_sum_case},
                COUNT(1) AS total
            FROM Locacao
            JOIN Veiculo ON Locacao.Veiculo = Veiculo.id
            JOIN Tenis ON Locacao.Tenis = Tenis.id
            JOIN Modelo ON Tenis.Modelo = Modelo.id
            GROUP BY bdate, nome_veiculo
            ORDER BY bdate DESC;
        """

        # Executar a consulta
        cur.execute(query)
        rows = cur.fetchall()
        columns = [desc[0] for desc in cur.description]
        cur.close()

        # Formatar os dados para JSON
        data = [dict(zip(columns, row)) for row in rows]

        return jsonify({"columns": columns, "data": data})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@admin.route('/admin/dashboard')
def dashboard():
    if 'logged_in' in session and session['logged_in']:
        return render_template('admin/8-dashboard.html')
    else:
        return redirect(url_for('admin.admin_login_page'))


@admin.route('/admin')
def redirect_admin():
    return redirect(url_for('admin.admin_login_page'))


@admin.route('/alive', methods=['GET'])
def is_alive():
    return "YES"
