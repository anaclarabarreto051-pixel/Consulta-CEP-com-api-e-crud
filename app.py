from pickle import APPEND
from flask import Flask, jsonify, request
import sqlite3
from flask_cors import CORS
CORS(app=Flask(__name__))
app = Flask(__name__)
DATABASE = 'database.db'
def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn
def create_table():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ceps (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cep TEXT NOT NULL,
            rua TEXT,
            bairro TEXT,
            cidade TEXT,
            estado TEXT
        )
    ''')
    conn.commit()
    conn.close()
create_table()

@app.route("/ceps", methods=["GET"])
def listar_ceps():
    conn = get_db_connection()
    ceps = conn.execute('SELECT * FROM ceps').fetchall()
    conn.close()
    return jsonify([dict(cep) for cep in ceps])

@app.route("/ceps", methods=["POST"])
def criar_cep():
    data=request.json
    conn = get_db_connection()
    conn.execute(
        "insert into ceps (cep, rua, cidade, estado, bairro) values (?, ?, ?, ?, ?)",
        data.get("cep"),
        data.get("rua"), 
        data.get("bairro"), 
        data.get("cidade"), 
        data.get("estado"),
    ),
    conn.commit()
    conn.close()
    return jsonify({"message": "CEP criado com sucesso!"}), 201

@app.route("/ceps/<cep>", methods=["GET"])
def buscar_cep(cep):
    conn = get_db_connection()
    cep_encontrado = conn.execute('SELECT * FROM ceps WHERE cep = ?', (cep,)).fetchone()
    conn.close()
    if cep_encontrado is None:
        return jsonify({"error": "CEP não encontrado"}), 404
    return jsonify(dict(cep_encontrado))

@app.route("/ceps/<cep>", methods=["PUT"])
def atualizar_cep(cep):
    data = request.json
    conn = get_db_connection()
    conn.execute(
        "UPDATE ceps SET rua = ?, bairro = ?, cidade = ?, estado = ? WHERE cep = ?",
        (
            data.get("rua"),
            data.get("bairro"),
            data.get("cidade"),
            data.get("estado"),
            cep,
        ),
    )
    conn.commit()
    conn.close()
    return jsonify({"message": "CEP atualizado com sucesso!"})

@app.route("/ceps/<cep>", methods=["DELETE"])
def deletar_cep(cep):
    conn = get_db_connection()
    conn.execute('DELETE FROM ceps WHERE cep = ?', (cep,))
    conn.commit()
    conn.close()
    return jsonify({"message": "CEP deletado com sucesso!"})

if __name__ == "__main__":
    app.run(debug=True)