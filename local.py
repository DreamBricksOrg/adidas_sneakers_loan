from flask import Blueprint, request, jsonify
from database import mysql
local = Blueprint('local', __name__)


@local.route('/locais', methods=['GET'])
def get_locais():
    cursor = mysql.connection.cursor()
    cursor.execute('SELECT * FROM Local')
    result = cursor.fetchall()
    return jsonify(result), 200

@local.route('/locais/<int:id>', methods=['GET'])
def get_local(id):
    cursor = mysql.connection.cursor()
    cursor.execute('SELECT * FROM Local WHERE id = %s', (id,))
    result = cursor.fetchone()
    return jsonify(result), 200 if result else 404

@local.route('/locais', methods=['POST'])
def create_local():
    data = request.get_json()
    nome = data.get('nome')
    if nome:
        cursor = mysql.connection.cursor()
        cursor.execute('INSERT INTO Local (nome) VALUES (%s)', (nome,))
        mysql.connection.commit()
        return jsonify({'message': 'Local criado com sucesso!'}), 201
    else:
        return jsonify({'error': 'O nome do local é obrigatório!'}), 400

@local.route('/locais/<int:id>', methods=['PUT'])
def update_local(id):
    data = request.get_json()
    nome = data.get('nome')
    if nome:
        cursor = mysql.connection.cursor()
        cursor.execute('UPDATE Local SET nome = %s WHERE id = %s', (nome, id))
        mysql.connection.commit()
        return jsonify({'message': 'Local atualizado com sucesso!'}), 200
    else:
        return jsonify({'error': 'O nome do local é obrigatório!'}), 400

@local.route('/locais/<int:id>', methods=['DELETE'])
def delete_local(id):
    cursor = mysql.connection.cursor()
    cursor.execute('DELETE FROM Local WHERE id = %s', (id,))
    mysql.connection.commit()
    return jsonify({'message': 'Local deletado com sucesso!'}), 200

