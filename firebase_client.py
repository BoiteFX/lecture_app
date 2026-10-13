import requests
import json

BASE_URL = "https://lecture-app-29464-default-rtdb.europe-west1.firebasedatabase.app"
DATA_URL = f"{BASE_URL}/data.json"

def charger_data():
    try:
        r = requests.get(DATA_URL)
        if r.status_code == 200:
            if r.text in ("null", "", None):
                return {"profils": [], "livres": []}

            data = json.loads(r.text)

            if not isinstance(data, dict):
                return {"profils": [], "livres": []}

            if "profils" not in data:
                data["profils"] = []
            if "livres" not in data:
                data["livres"] = []

            return data

        return {"profils": [], "livres": []}
    except Exception:
        return {"profils": [], "livres": []}

def sauvegarder_data(data):
    try:
        requests.put(DATA_URL, json=data)
    except Exception:
        pass
