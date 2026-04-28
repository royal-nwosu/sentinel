import json
import os
from models import User, Disaster

DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
USERS_FILE = os.path.join(DATA_DIR, 'users.json')
DISASTERS_FILE = os.path.join(DATA_DIR, 'disasters.json')

def ensure_data_dir():
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)

def load_users():
    ensure_data_dir()
    if not os.path.exists(USERS_FILE):
        return []
    with open(USERS_FILE, 'r') as f:
        data = json.load(f)
        return [User(u['username'], u['password']) for u in data]

def load_disasters():
    ensure_data_dir()
    if not os.path.exists(DISASTERS_FILE):
        return {}
    with open(DISASTERS_FILE, 'r') as f:
        data = json.load(f)
        # Store in a dictionary mapped by event_id
        return {d['event_id']: Disaster.from_dict(d) for d in data}

def save_disasters(disasters_dict):
    ensure_data_dir()
    data = [d.to_dict() for d in disasters_dict.values()]
    with open(DISASTERS_FILE, 'w') as f:
        json.dump(data, f, indent=2)
