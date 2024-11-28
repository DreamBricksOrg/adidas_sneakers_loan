from flask import Blueprint, request, jsonify
from config.database import mysql
veiculo = Blueprint('veiculo', __name__)


@veiculo.route('/veiculos', methods=['GET'])
def get_locais():
    cursor = mysql.connection.cursor()
    cursor.execute('SELECT * FROM Veiculo')
    result = cursor.fetchall()
    return jsonify(result), 200

@veiculo.route('/veiculos/<int:id>', methods=['GET'])
def get_local(id):
    cursor = mysql.connection.cursor()
    cursor.execute('SELECT * FROM Veiculo WHERE id = %s', (id,))
    result = cursor.fetchone()
    return jsonify(result), 200 if result else 404

@veiculo.route('/veiculos', methods=['POST'])
def create_local():
    data = request.get_json()
    nome = data.get('nome')
    if nome:
        cursor = mysql.connection.cursor()
        cursor.execute('INSERT INTO Veiculo (nome) VALUES (%s)', (nome,))
        mysql.connection.commit()
        return jsonify({'message': 'Veiculo criado com sucesso!'}), 201
    else:
        return jsonify({'error': 'O nome do veiculo é obrigatório!'}), 400

@veiculo.route('/veiculos/<int:id>', methods=['PUT'])
def update_local(id):
    data = request.get_json()
    nome = data.get('nome')
    if nome:
        cursor = mysql.connection.cursor()
        cursor.execute('UPDATE Veiculo SET nome = %s WHERE id = %s', (nome, id))
        mysql.connection.commit()
        return jsonify({'message': 'Veiculo atualizado com sucesso!'}), 200
    else:
        return jsonify({'error': 'O nome do veiculo é obrigatório!'}), 400

@veiculo.route('/veiculos/<int:id>', methods=['DELETE'])
def delete_local(id):
    cursor = mysql.connection.cursor()
    cursor.execute('DELETE FROM Veiculo WHERE id = %s', (id,))
    mysql.connection.commit()
    return jsonify({'message': 'Veiculo deletado com sucesso!'}), 200

