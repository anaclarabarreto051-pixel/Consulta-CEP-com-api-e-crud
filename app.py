import sqlite3
import requests
from flask import Flask, jsonify, request
from flask_cors import CORS
app = Flask(__name__)
CORS(app)
DATABASE = 'database.db'
# banco de dados SQLite
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

#rotas da API
#listar todos os ceps
@app.route("/ceps", methods=["GET"])
def listar_ceps():
    conn = get_db_connection()
    ceps = conn.execute('SELECT * FROM ceps').fetchall()
    conn.close()
    return jsonify([dict(cep) for cep in ceps])

#criar um novo cep manualmente
@app.route("/ceps", methods=["POST"])
def criar_cep():
    data = request.get_json()
    if not data or "cep" not in data:
        return jsonify({"error": "JSON inválido"}), 400
    
    conn = get_db_connection()
    try: 
        conn.execute(
            "INSERT INTO ceps (cep, rua, bairro, cidade, estado) VALUES (?, ?, ?, ?, ?)",
            (
                data.get("cep"),
                data.get("rua"), 
                data.get("bairro"), 
                data.get("cidade"), 
                data.get("estado"),
            ),
        )
        conn.commit()
    except sqlite3.IntegrityError:
        return jsonify({"error": "CEP já existe"}), 409
    finally:
        conn.close()
    return jsonify({"message": "CEP criado com sucesso!"}), 201

#buscar um cep automáticomente via API externa
@app.route("/ceps/<cep>", methods=["GET"])
def buscar_cep(cep):
    # Verificar se o CEP já está no banco de dados
    conn = get_db_connection()
    cep_encontrado = conn.execute('SELECT * FROM ceps WHERE cep = ?', (cep,)).fetchone()

    if cep_encontrado: 
        conn.close()
        return jsonify(dict(cep_encontrado)), 200
    # Buscar na API externa se não encontrado no banco
    response = requests.get(f"https://viacep.com.br/ws/{cep}/json/")
    if response.status_code != 200 or response.json().get("erro"):
        conn.close()
        return jsonify({"error": "Erro ao consultar o ViaCEP"}), 502
    
    data = response.json()

    # Salvar no banco de dados
    conn.execute(
        "INSERT INTO ceps (cep, rua, bairro, cidade, estado) VALUES (?, ?, ?, ?, ?)",
        ( 
            data.get("cep"),
            data.get("logradouro"),
            data.get("bairro"),
            data.get("localidade"),
            data.get("uf"),
        ),
    )
    conn.commit()
    conn.close()
    # Retornar os dados do CEP      
    return jsonify({
        "cep": cep,
        "rua": data.get("logradouro"),
        "bairro": data.get("bairro"),
        "cidade": data.get("localidade"),
        "estado": data.get("uf"),
    }), 200

#atualizar um cep
@app.route("/ceps/<cep>", methods=["PUT"])
def atualizar_cep(cep):
    data = request.get_json()
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

#deletar um cep
@app.route("/ceps/<cep>", methods=["DELETE"])
def deletar_cep(cep):
    conn = get_db_connection()
    conn.execute('DELETE FROM ceps WHERE cep = ?', (cep,))
    conn.commit()
    conn.close()
    return jsonify({"message": "CEP deletado com sucesso!"})

if __name__ == "__main__":
    app.run(debug=True)