from flask import Flask, request, jsonify
import os
from PyP100 import PyP110, PyL530

app = Flask(__name__)

# Identifiants Tapo depuis les variables d’environnement Railway
TAPO_EMAIL = os.getenv("TAPO_EMAIL")
TAPO_PASSWORD = os.getenv("TAPO_PASSWORD")

# Déclaration des appareils
TAPO_DEVICES = {
    "lampe_salon": {"ip": "192.168.1.22", "type": "L530"},
    "lampe_piece1": {"ip": "192.168.1.23", "type": "L530"},
    "lampe_piece2": {"ip": "192.168.1.21", "type": "L530"},
    "prise_piece_de_vie": {"ip": "192.168.1.24", "type": "P110"}
}

@app.route('/')
def index():
    return jsonify({"message": "API opérationnelle avec contrôle Tapo."})

@app.route('/tapo', methods=['POST'])
def control_tapo():
    data = request.json
    device_name = data.get("device_name")
    action = data.get("action")  # 'on' ou 'off'

    if not device_name or not action:
        return jsonify({"error": "device_name et action sont requis"}), 400

    device_info = TAPO_DEVICES.get(device_name)
    if not device_info:
        return jsonify({"error": "Nom d'appareil inconnu"}), 400

    ip = device_info["ip"]
    device_type = device_info["type"]

    try:
        if device_type == "L530":
            device = PyL530.PyL530(TAPO_EMAIL, TAPO_PASSWORD, ip)
        elif device_type == "P110":
            device = PyP110.PyP110(TAPO_EMAIL, TAPO_PASSWORD, ip)
        else:
            return jsonify({"error": "Type d'appareil non supporté"}), 400

        device.handshake()
        device.login()

        if action == "on":
            device.turnOn()
        elif action == "off":
            device.turnOff()
        else:
            return jsonify({"error": "Action invalide"}), 400

        return jsonify({"message": f"{device_name} mis à {action} avec succès."})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=os.getenv("PORT", default=5000))
