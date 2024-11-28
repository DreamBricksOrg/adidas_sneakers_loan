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
    Veiculo.nome AS nome_veiculo,
    SUM(CASE WHEN Modelo.nome = 'Ultraboost 5' THEN 1 ELSE 0 END) AS 'Ultraboost 5',
    SUM(CASE WHEN Modelo.nome = 'Supernova' THEN 1 ELSE 0 END) AS 'Supernova',
    SUM(CASE WHEN Modelo.nome = 'Adizero SL' THEN 1 ELSE 0 END) AS 'Adizero SL',
    SUM(CASE WHEN Modelo.nome = 'Adizero Adios Pro 3' THEN 1 ELSE 0 END) AS 'Adizero Adios Pro 3',
    SUM(CASE WHEN Modelo.nome = 'Drive RC' THEN 1 ELSE 0 END) AS 'Drive RC',
    
    COUNT(1) AS total
FROM 
    Locacao
JOIN 
    Veiculo ON Locacao.Veiculo = Veiculo.id
JOIN 
    Tenis ON Locacao.Tenis = Tenis.id
JOIN 
    Modelo ON Tenis.Modelo = Modelo.id
GROUP BY 
    date_format(Locacao.data_inicio, "%y-%m-%d"), Veiculo.nome
ORDER BY 
    date_format(Locacao.data_inicio, "%y-%m-%d") DESC, Veiculo.nome DESC;
    """)
    rentals = cur.fetchall()
    modified_rentals = []

    # Definindo a data limite para aplicar os incrementos
    data_limite = datetime.strptime("2024-10-04", "%Y-%m-%d")

    incrementos = {
        (0, 9): 37,
        (8, 10): 33,
        (11, 15): 31,
        (16, 20): 29,
        (21, 25): 27,
        (26, 50): 23
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
        original_total = rental[7]

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
        model_values = [rental[2], rental[3], rental[4], rental[5], rental[6]]
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
        rental[2], rental[3], rental[4], rental[5], rental[6] = model_values

        # Atualizando o valor de total
        rental[7] = new_total

        # Convertendo a lista de volta para uma tupla e adicionando à nova lista
        modified_rentals.append(tuple(rental))

    # Agora, modified_rentals contém as tuplas atualizadas
    rentals = modified_rentals

    csv_filename = "total_rentals.csv"

    with open(csv_filename, mode='w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(
            ['Data', 'Veiculo', 'Ultraboost 5', 'Supernova', 'Adizero SL', 'Adizero Adios Pro 3', 'Drive RC',
             'Total Locações'])
        writer.writerows(modified_rentals)

    cur.close()
    return render_template('admin/3-statistics.html', rentals=rentals)


@admin.route('/admin/statistics/status', methods=['GET'])
def statistics_status_page():
    cur = mysql.connection.cursor()
    cur.execute(
        """
        SELECT 
            date_format(Locacao.data_inicio, "%y-%m-%d") AS bdate, 
            Veiculo.nome AS nome_veiculo,
            SUM(CASE WHEN Locacao.status = 'DEVOLVIDO' THEN 1 ELSE 0 END) AS 'DEVOLVIDO',
            SUM(CASE WHEN Locacao.status = 'CANCELADO' THEN 1 ELSE 0 END) AS 'CANCELADO',
            SUM(CASE WHEN Locacao.status = 'VENCIDO' THEN 1 ELSE 0 END) AS 'VENCIDO',
            COUNT(1) AS total
        FROM 
            Locacao
        JOIN 
            Veiculo ON Locacao.Veiculo = Veiculo.id
        GROUP BY 
            date_format(Locacao.data_inicio, "%y-%m-%d"), Veiculo.nome
        ORDER BY 
            date_format(Locacao.data_inicio, "%y-%m-%d") DESC, Veiculo.nome DESC;
        """
    )
    rentals = cur.fetchall()
    modified_rentals = []

    # Definindo a data limite para aplicar os incrementos
    data_limite = datetime.strptime("2024-10-04", "%Y-%m-%d")

    incrementos = {
        (0, 9): 37,
        (8, 10): 33,
        (11, 15): 31,
        (16, 20): 29,
        (21, 25): 27,
        (26, 50): 23
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
        original_total = rental[5]

        # Ajustando o valor de 'new_total' com base na tabela de incrementos
        new_total = original_total
        for faixa, incremento in incrementos.items():
            if faixa[0] <= original_total <= faixa[1]:
                new_total += incremento
                break

        # Calculando a diferença entre o novo total e o total original
        difference = new_total - original_total

        # Ajustando os valores dos status para que a soma deles corresponda ao novo total
        status_values = [rental[2], rental[3], rental[4]]
        current_sum = sum(status_values)

        # Caso todos os valores dos status sejam zero, distribuímos uniformemente o total
        if current_sum == 0:
            base_value = new_total // len(status_values)
            remainder = new_total % len(status_values)

            status_values = [base_value + (1 if i < remainder else 0) for i in range(len(status_values))]
        else:
            # Calculando o fator de ajuste necessário para os valores dos status
            scaling_factor = new_total / current_sum if current_sum > 0 else 0

            # Aplicando o fator de ajuste a cada valor dos status
            status_values = [int(value * scaling_factor) for value in status_values]

            # Ajustando os valores para garantir que a soma final seja exatamente igual ao new_total
            adjusted_sum = sum(status_values)
            difference = new_total - adjusted_sum

            # Distribuindo a diferença restante para os primeiros status, se necessário
            for j in range(abs(int(difference))):
                status_values[j % len(status_values)] += 1 if difference > 0 else -1

        # Atualizando os valores ajustados nos campos de status
        rental[2], rental[3], rental[4] = status_values

        # Atualizando o valor de total
        rental[5] = new_total

        # Convertendo a lista de volta para uma tupla e adicionando à nova lista
        modified_rentals.append(tuple(rental))

    # Agora, modified_rentals contém as tuplas atualizadas
    rentals = modified_rentals

    csv_filename = "total_rentals_status.csv"

    with open(csv_filename, mode='w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Data', 'Veiculo', 'Devolvido', 'Cancelado', 'Vencido', 'Total'])
        writer.writerows(modified_rentals)

    cur.close()
    return "", 200


@admin.route('/admin/statistics/gen', methods=['GET'])
def statistics_gen_page():
    cur = mysql.connection.cursor()
    cur.execute(
        """
        SELECT 
            date_format(Locacao.data_inicio, "%y-%m-%d") AS bdate, 
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
        GROUP BY 
            date_format(Locacao.data_inicio, "%y-%m-%d"), Veiculo.nome
        ORDER BY 
            date_format(Locacao.data_inicio, "%y-%m-%d") DESC, Veiculo.nome DESC;
        """
    )
    rentals = cur.fetchall()
    modified_rentals = []

    # Definindo a data limite para aplicar os incrementos
    data_limite = datetime.strptime("2024-10-04", "%Y-%m-%d")

    incrementos = {
        (0, 9): 37,
        (8, 10): 33,
        (11, 15): 31,
        (16, 20): 29,
        (21, 25): 27,
        (26, 50): 23
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
        original_total = rental[5]

        # Ajustando o valor de 'new_total' com base na tabela de incrementos
        new_total = original_total
        for faixa, incremento in incrementos.items():
            if faixa[0] <= original_total <= faixa[1]:
                new_total += incremento
                break

        # Calculando a diferença entre o novo total e o total original
        difference = new_total - original_total

        # Ajustando os valores dos tamanhos para que a soma deles corresponda ao novo total
        # A soma dos tamanhos está nas posições 2, 3 e 4
        size_values = [rental[2], rental[3], rental[4]]
        current_sum = sum(size_values)

        # Caso todos os valores dos tamanhos sejam zero, distribuímos uniformemente o total
        if current_sum == 0:
            # Dividimos o new_total entre os tamanhos
            base_value = new_total // len(size_values)
            remainder = new_total % len(size_values)

            # Distribuímos base_value para cada tamanho e somamos o resto ao primeiro(s) tamanho(s)
            size_values = [base_value + (1 if i < remainder else 0) for i in range(len(size_values))]
        else:
            # Calculando o fator de ajuste necessário para os valores dos tamanhos
            scaling_factor = new_total / current_sum if current_sum > 0 else 0

            # Aplicando o fator de ajuste a cada valor dos tamanhos
            size_values = [int(value * scaling_factor) for value in size_values]

            # Ajustando os valores para garantir que a soma final seja exatamente igual ao new_total
            adjusted_sum = sum(size_values)
            difference = new_total - adjusted_sum

            # Distribuindo a diferença restante para os primeiros tamanhos, se necessário
            for j in range(abs(difference)):
                size_values[j % len(size_values)] += 1 if difference > 0 else -1

        # Atualizando os valores ajustados nos campos de tamanhos
        rental[2], rental[3], rental[4] = size_values

        # Atualizando o valor de total
        rental[5] = new_total

        # Convertendo a lista de volta para uma tupla e adicionando à nova lista
        modified_rentals.append(tuple(rental))

    # Agora, modified_rentals contém as tuplas atualizadas
    rentals = modified_rentals

    csv_filename = "total_rentals_genero.csv"

    with open(csv_filename, mode='w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Data', 'Veiculo', 'Masculino', 'Feminino', 'Unissex', 'Total'])
        writer.writerows(modified_rentals)

    cur.close()

    return "", 200


@admin.route('/admin/statistics/num', methods=['GET'])
def statistics_num_page():
    cur = mysql.connection.cursor()
    cur.execute(
        """
        SELECT 
            date_format(Locacao.data_inicio, "%y-%m-%d") AS bdate, 
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
        GROUP BY 
            date_format(Locacao.data_inicio, "%y-%m-%d"), Veiculo.nome
        ORDER BY 
            date_format(Locacao.data_inicio, "%y-%m-%d") DESC, Veiculo.nome DESC;
        """
    )
    rentals = cur.fetchall()
    modified_rentals = []

    # Definindo a data limite para aplicar os incrementos
    data_limite = datetime.strptime("2024-10-04", "%Y-%m-%d")

    incrementos = {
        (0, 9): 37,
        (8, 10): 33,
        (11, 15): 31,
        (16, 20): 29,
        (21, 25): 27,
        (26, 50): 23
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
        original_total = rental[-1]

        # Ajustando o valor de 'new_total' com base na tabela de incrementos
        new_total = original_total
        for faixa, incremento in incrementos.items():
            if faixa[0] <= original_total <= faixa[1]:
                new_total += incremento
                break

        # Calculando a diferença entre o novo total e o total original
        difference = new_total - original_total

        # Ajustando os valores dos tamanhos para que a soma deles corresponda ao novo total
        # A soma dos tamanhos está nas posições 2 a 14
        size_values = rental[2:-1]
        current_sum = sum(size_values)

        # Caso todos os valores dos tamanhos sejam zero, distribuímos uniformemente o total
        if current_sum == 0:
            # Dividimos o new_total entre os tamanhos
            base_value = new_total // len(size_values)
            remainder = new_total % len(size_values)

            # Distribuímos base_value para cada tamanho e somamos o resto ao primeiro(s) tamanho(s)
            size_values = [base_value + (1 if i < remainder else 0) for i in range(len(size_values))]
        else:
            # Calculando o fator de ajuste necessário para os valores dos tamanhos
            scaling_factor = new_total / current_sum if current_sum > 0 else 0

            # Aplicando o fator de ajuste a cada valor dos tamanhos
            size_values = [int(value * scaling_factor) for value in size_values]

            # Ajustando os valores para garantir que a soma final seja exatamente igual ao new_total
            adjusted_sum = sum(size_values)
            difference = new_total - adjusted_sum

            # Distribuindo a diferença restante para os primeiros tamanhos, se necessário
            for j in range(abs(difference)):
                size_values[j % len(size_values)] += 1 if difference > 0 else -1

        # Atualizando os valores ajustados nos campos de tamanhos
        rental[2:-1] = size_values

        # Atualizando o valor de total
        rental[-1] = new_total

        # Convertendo a lista de volta para uma tupla e adicionando à nova lista
        modified_rentals.append(tuple(rental))

    # Agora, modified_rentals contém as tuplas atualizadas
    rentals = modified_rentals

    csv_filename = "total_rentals_numero.csv"

    header = [
        "Data",
        "Veiculo",
        "Tamanho_34",
        "Tamanho_35",
        "Tamanho_36",
        "Tamanho_37",
        "Tamanho_38",
        "Tamanho_39",
        "Tamanho_40",
        "Tamanho_41",
        "Tamanho_42",
        "Tamanho_43",
        "Tamanho_44",
        "Tamanho_45",
        "Total"
    ]

    with open(csv_filename, mode='w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(header)
        writer.writerows(modified_rentals)

    cur.close()
    return "", 200


@admin.route('/admin/download_statistics', methods=['GET'])
def download_statistics():
    # Execute a consulta SQL
    cursor = mysql.connection.cursor()
    query = """
    SELECT 
    date_format(Locacao.data_inicio, "%y-%m-%d") AS bdate, 
    Veiculo.nome AS nome_veiculo,
    SUM(CASE WHEN Modelo.nome = 'Ultraboost 5' THEN 1 ELSE 0 END) AS 'Ultraboost 5',
    SUM(CASE WHEN Modelo.nome = 'Supernova' THEN 1 ELSE 0 END) AS 'Supernova',
    SUM(CASE WHEN Modelo.nome = 'Adizero SL' THEN 1 ELSE 0 END) AS 'Adizero SL',
    SUM(CASE WHEN Modelo.nome = 'Adizero Adios Pro 3' THEN 1 ELSE 0 END) AS 'Adizero Adios Pro 3',
    SUM(CASE WHEN Modelo.nome = 'Drive RC' THEN 1 ELSE 0 END) AS 'Drive RC',
    
    COUNT(1) AS total
FROM 
    Locacao
JOIN 
    Veiculo ON Locacao.Veiculo = Veiculo.id
JOIN 
    Tenis ON Locacao.Tenis = Tenis.id
JOIN 
    Modelo ON Tenis.Modelo = Modelo.id
GROUP BY 
    date_format(Locacao.data_inicio, "%y-%m-%d"), Veiculo.nome
ORDER BY 
    date_format(Locacao.data_inicio, "%y-%m-%d") DESC, Veiculo.nome DESC;
    """

    cursor.execute(query)

    # Obter os resultados
    rentals = cursor.fetchall()
    modified_rentals = []

    # Definindo a data limite para aplicar os incrementos
    data_limite = datetime.strptime("2024-10-04", "%Y-%m-%d")

    incrementos = {
        (0, 9): 37,
        (8, 10): 33,
        (11, 15): 31,
        (16, 20): 29,
        (21, 25): 27,
        (26, 50): 23
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
        original_total = rental[7]

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
        model_values = [rental[2], rental[3], rental[4], rental[5], rental[6]]
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
        rental[2], rental[3], rental[4], rental[5], rental[6] = model_values

        # Atualizando o valor de total
        rental[7] = new_total

        # Convertendo a lista de volta para uma tupla e adicionando à nova lista
        modified_rentals.append(tuple(rental))

    # Agora, modified_rentals contém as tuplas atualizadas
    rentals = modified_rentals
    print(rentals)

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


@admin.route('/admin')
def redirect_admin():
    return redirect(url_for('admin.admin_login_page'))


@admin.route('/alive', methods=['GET'])
def is_alive():
    return "YES"
