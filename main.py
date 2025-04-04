# main.py

from flask import Flask, request, jsonify
import os
# IMPORTANT: L'import se fait bien avec PyP100 (majuscules), même si le paquet pip s'appelle pyp100
from PyP100 import PyP110, PyL530

app = Flask(__name__)

# --- Configuration ---

# Identifiants Tapo depuis les variables d’environnement Railway
TAPO_EMAIL = os.getenv("TAPO_EMAIL")
TAPO_PASSWORD = os.getenv("TAPO_PASSWORD")

# Déclaration des appareils
# ATTENTION: Les adresses IP locales (192.168.x.x) ne seront PAS accessibles
#            depuis le conteneur Railway hébergé dans le cloud.
#            Cette API ne fonctionnera QUE si elle est exécutée sur le MÊME
#            réseau local que les appareils Tapo, ou si les appareils
#            ont des IP publiques/sont accessibles via un tunnel/VPN.
TAPO_DEVICES = {
    "lampe_salon": {"ip": "192.168.1.22", "type": "L530"},
    "lampe_piece1": {"ip": "192.168.1.23", "type": "L530"},
    "lampe_piece2": {"ip": "192.168.1.21", "type": "L530"},
    "prise_piece_de_vie": {"ip": "192.168.1.24", "type": "P110"}
}

# --- Routes API ---

@app.route('/')
def index():
    """Route d'accueil simple pour vérifier que l'API est en ligne."""
    return jsonify({"message": "API opérationnelle avec contrôle Tapo."})

@app.route('/tapo', methods=['POST'])
def control_tapo():
    """Contrôle un appareil Tapo (allumer/éteindre)."""
    if not TAPO_EMAIL or not TAPO_PASSWORD:
        return jsonify({"error": "Variables d'environnement TAPO_EMAIL et TAPO_PASSWORD manquantes"}), 500

    data = request.json
    if not data:
        return jsonify({"error": "Corps de la requête JSON manquant"}), 400

    device_name = data.get("device_name")
    action = data.get("action")  # Doit être 'on' ou 'off'

    if not device_name or not action:
        return jsonify({"error": "Les champs 'device_name' et 'action' sont requis dans le JSON"}), 400

    device_info = TAPO_DEVICES.get(device_name)
    if not device_info:
        return jsonify({"error": f"Nom d'appareil inconnu : {device_name}"}), 400

    ip = device_info["ip"]
    device_type = device_info["type"]
    action = action.lower() # S'assurer que l'action est en minuscules

    try:
        # Instanciation de l'appareil basé sur son type
        if device_type == "L530":
            device = PyL530.L530Device(ip, TAPO_EMAIL, TAPO_PASSWORD) # Correction nom classe L530
        elif device_type == "P110":
            device = PyP110.P110Device(ip, TAPO_EMAIL, TAPO_PASSWORD) # Correction nom classe P110
        else:
            return jsonify({"error": f"Type d'appareil non supporté : {device_type}"}), 400

        # Connexion et authentification
        device.login() # login() fait aussi le handshake dans les versions récentes

        # Exécution de l'action demandée
        if action == "on":
            device.turn_on() # Méthode renommée en turn_on
        elif action == "off":
            device.turn_off() # Méthode renommée en turn_off
        else:
            return jsonify({"error": "Action invalide. Utilisez 'on' ou 'off'."}), 400

        return jsonify({"message": f"'{device_name}' ({ip}) a été mis à '{action}' avec succès."})

    except Exception as e:
        # Capturer les erreurs potentielles (connexion réseau, authentification, etc.)
        error_message = f"Erreur lors du contrôle de '{device_name}': {str(e)}"
        print(f"ERREUR: {error_message}") # Log pour le débogage côté serveur
        return jsonify({"error": error_message}), 500

# --- Démarrage (pour tests locaux, Gunicorn gère sur Railway) ---
if __name__ == '__main__':
    # Utilise le port défini par l'environnement (standard pour Railway/Heroku) ou 5000 par défaut
    port = int(os.environ.get('PORT', 5000))
    # Ne pas utiliser debug=True en production
    app.run(host='0.0.0.0', port=port)
