from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Permite la comunicación con el HTML local

# Variable en memoria para guardar los platillos
platillos = []

@app.route('/api/platillos', methods=['POST'])
def agregar_platillo():
    data = request.get_json()
    if data:
        platillos.append(data)
        print("▶ Nuevo platillo recibido desde n8n:", data)
        return jsonify({"status": "success", "message": "Platillo recibido"}), 200
    return jsonify({"status": "error"}), 400

@app.route('/api/platillos', methods=['GET'])
def obtener_platillos():
    return jsonify(platillos), 200

if __name__ == '__main__':
    print("🚀 Servidor local listo en http://localhost:5000")
    app.run(port=5000, debug=True)