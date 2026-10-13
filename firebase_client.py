import requests
import json

# URL de ta base Firebase (sans le # à la fin)
BASE_URL = "https://lecture-app-29464-default-rtdb.europe-west1.firebasedatabase.app"

DATA_URL = f"{BASE_URL}/data.json"

def charger_data():
    try:
        r = requests.get(DATA_URL)
        if r.status_code == 200 and r.text:
            return json.loads(r.text)
        return {"profils": [], "livres": []}
    except Exception:
        return {"profils": [], "livres": []}

def sauvegarder_data(data):
    try:
        requests.put(DATA_URL, json=data)
    except Exception:
        pass
