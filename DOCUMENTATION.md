# Sentinel — Disaster Tracking System Documentation

## Table of Contents
1. [Overview](#overview)
2. [Architecture](#architecture)
3. [File Structure](#file-structure)
4. [Backend Code](#backend-code)
5. [Frontend Code](#frontend-code)
6. [Running the Application](#running-the-application)

---

## Overview

Sentinel is a full-stack web application for tracking and managing disaster events. It features a Three.js animated login screen, a premium glassmorphism dashboard with Chart.js visualizations, and full CRUD operations backed by a Flask API with JSON file storage.

**Tech Stack:** Python/Flask, HTML5, CSS3, JavaScript, Chart.js, Three.js

---

## Architecture

```
Browser (HTML/CSS/JS)
    ├── Login View (Three.js planet + clouds)
    └── Dashboard View
        ├── Overview Tab (KPI cards, bar chart, deadliest table)
        └── Records Tab (CRUD table, search, modal form)
            │
            ▼
Flask API (app.py)
    ├── /api/login, /api/logout, /api/check_auth
    ├── /api/dashboard
    └── /api/disasters
            │
            ▼
SystemManager (manager.py) → Storage (storage.py) → data/disasters.json
```

---

## File Structure

```
sentinel/
├── app.py              # Flask routes and API endpoints
├── auth.py             # Authentication logic
├── manager.py          # Business logic (SystemManager class)
├── models.py           # Data models (User, Disaster)
├── storage.py          # JSON file persistence
├── data/
│   ├── users.json      # User credentials
│   └── disasters.json  # Disaster records
├── static/
│   ├── index.css       # Dashboard and login styles
│   └── app.js          # Frontend JavaScript logic
└── templates/
    └── index.html      # Single-page HTML template
```

---

## Backend Code

### app.py — Flask Routes

```python
from flask import Flask, render_template, request, jsonify, session
import os
from auth import authenticate
from manager import SystemManager

app = Flask(__name__)
app.secret_key = os.urandom(24)

manager = SystemManager()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    if authenticate(username, password):
        session['logged_in'] = True
        return jsonify({'success': True})
    return jsonify({'success': False, 'message': 'Invalid credentials'}), 401

@app.route('/api/logout', methods=['POST'])
def logout():
    session.pop('logged_in', None)
    return jsonify({'success': True})

@app.route('/api/check_auth', methods=['GET'])
def check_auth():
    return jsonify({'logged_in': session.get('logged_in', False)})

@app.route('/api/dashboard', methods=['GET'])
def get_dashboard():
    if not session.get('logged_in'):
        return jsonify({'error': 'Unauthorized'}), 401
    stats = manager.get_dashboard_stats()
    def serialize_disaster(d):
        if d is None: return None
        return d.to_dict()
    return jsonify({
        'total': stats['total'],
        'active': stats['active'],
        'highest_magnitude': serialize_disaster(stats['highest_magnitude']),
        'most_affected_region': stats['most_affected_region'],
        'deadliest': [serialize_disaster(d) for d in stats['deadliest']]
    })

@app.route('/api/disasters', methods=['GET', 'POST'])
def disasters_endpoint():
    if not session.get('logged_in'):
        return jsonify({'error': 'Unauthorized'}), 401
    if request.method == 'GET':
        search_term = request.args.get('search', '')
        if search_term:
            results = manager.search_disasters(search_term)
        else:
            results = manager.get_all_disasters()
        return jsonify([d.to_dict() for d in results])
    if request.method == 'POST':
        data = request.get_json()
        try:
            manager.add_disaster(
                data['event_id'], data['name'], data['type'],
                data['region'], data['country'], data['date'],
                data['magnitude'], data['casualties'], data['status']
            )
            return jsonify({'success': True})
        except ValueError as e:
            return jsonify({'success': False, 'message': str(e)}), 400

@app.route('/api/disasters/<event_id>', methods=['PUT', 'DELETE'])
def disaster_detail(event_id):
    if not session.get('logged_in'):
        return jsonify({'error': 'Unauthorized'}), 401
    if request.method == 'DELETE':
        if manager.delete_disaster(event_id):
            return jsonify({'success': True})
        return jsonify({'success': False, 'message': 'Not found'}), 404
    if request.method == 'PUT':
        updates = request.get_json()
        try:
            manager.update_disaster(event_id, **updates)
            return jsonify({'success': True})
        except (KeyError, ValueError) as e:
            return jsonify({'success': False, 'message': str(e)}), 400

if __name__ == '__main__':
    app.run(debug=True, port=5000)
```

---

### auth.py — Authentication

```python
from storage import load_users

def authenticate(username, password):
    users = load_users()
    for user in users:
        if user.username == username and user.password == password:
            return True
    return False
```

---

### models.py — Data Models

```python
class User:
    def __init__(self, username, password):
        self.username = username
        self.password = password

class Disaster:
    def __init__(self, event_id, name, type, region, country,
                 date, magnitude, casualties, status):
        self.event_id = event_id
        self.name = name
        self.type = type
        self.region = region
        self.country = country
        self.date = date
        self.magnitude = float(magnitude)
        self.casualties = int(casualties)
        self.status = status

    def to_dict(self):
        return {
            "event_id": self.event_id,
            "name": self.name,
            "type": self.type,
            "region": self.region,
            "country": self.country,
            "date": self.date,
            "magnitude": self.magnitude,
            "casualties": self.casualties,
            "status": self.status
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            data["event_id"], data["name"], data["type"],
            data["region"], data["country"], data["date"],
            data["magnitude"], data["casualties"], data["status"]
        )
```

---

### storage.py — JSON Persistence

```python
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
        return {d['event_id']: Disaster.from_dict(d) for d in data}

def save_disasters(disasters_dict):
    ensure_data_dir()
    data = [d.to_dict() for d in disasters_dict.values()]
    with open(DISASTERS_FILE, 'w') as f:
        json.dump(data, f, indent=2)
```

---

### manager.py — Business Logic

```python
from models import Disaster
from storage import load_disasters, save_disasters

class SystemManager:
    def __init__(self):
        self.disasters = load_disasters()

    def get_all_disasters(self):
        return list(self.disasters.values())

    def add_disaster(self, event_id, name, type_val, region, country,
                     date, magnitude, casualties, status):
        if event_id in self.disasters:
            raise ValueError(f"Event ID {event_id} already exists.")
        try:
            magnitude_val = float(magnitude)
            casualties_val = int(casualties)
        except ValueError:
            raise ValueError("Magnitude must be a number and casualties must be an integer.")
        d = Disaster(event_id, name, type_val, region, country,
                     date, magnitude_val, casualties_val, status)
        self.disasters[event_id] = d
        save_disasters(self.disasters)

    def update_disaster(self, event_id, **kwargs):
        if event_id not in self.disasters:
            raise KeyError(f"Event ID {event_id} not found.")
        d = self.disasters[event_id]
        if 'magnitude' in kwargs:
            try: d.magnitude = float(kwargs['magnitude'])
            except ValueError: raise ValueError("Magnitude must be a number.")
        if 'casualties' in kwargs:
            try: d.casualties = int(kwargs['casualties'])
            except ValueError: raise ValueError("Casualties must be an integer.")
        for k, v in kwargs.items():
            if k not in ['magnitude', 'casualties']:
                setattr(d, k, v)
        save_disasters(self.disasters)

    def delete_disaster(self, event_id):
        if event_id in self.disasters:
            del self.disasters[event_id]
            save_disasters(self.disasters)
            return True
        return False

    def search_disasters(self, search_term):
        results = []
        term = search_term.lower()
        for d in self.disasters.values():
            if (term in d.name.lower() or term in d.type.lower() or
                term in d.region.lower() or term in d.country.lower() or
                term in d.status.lower()):
                results.append(d)
        return results

    def get_dashboard_stats(self):
        total = len(self.disasters)
        active = sum(1 for d in self.disasters.values()
                     if d.status.lower() == 'active')
        if total > 0:
            highest_mag = max(self.disasters.values(),
                              key=lambda x: x.magnitude)
            regions = {}
            for d in self.disasters.values():
                regions[d.region] = regions.get(d.region, 0) + 1
            most_affected_region = max(regions, key=regions.get)
        else:
            highest_mag = None
            most_affected_region = "N/A"
        deadliest = sorted(self.disasters.values(),
                           key=lambda x: x.casualties, reverse=True)[:5]
        return {
            "total": total,
            "active": active,
            "highest_magnitude": highest_mag,
            "most_affected_region": most_affected_region,
            "deadliest": deadliest
        }
```

---

## Frontend Code

### static/app.js — Client-Side Logic

```javascript
document.addEventListener('DOMContentLoaded', () => {

    let chartInstance = null;

    // Check Auth Status on Load
    fetch('/api/check_auth')
        .then(r => r.json())
        .then(data => {
            if (data.logged_in) showDashboard();
            else showLogin();
        });

    // Login Form
    document.getElementById('login-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        const username = document.getElementById('username').value;
        const password = document.getElementById('password').value;
        const errorMsg = document.getElementById('login-error');
        try {
            const res = await fetch('/api/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, password })
            });
            const data = await res.json();
            if (data.success) { errorMsg.textContent = ''; showDashboard(); }
            else { errorMsg.textContent = data.message || 'Login failed'; }
        } catch (err) { errorMsg.textContent = 'Server error'; }
    });

    // Logout
    document.getElementById('logout-btn').addEventListener('click', async () => {
        await fetch('/api/logout', { method: 'POST' });
        showLogin();
    });

    // Navigation
    document.querySelectorAll('.nav-tab').forEach(btn => {
        btn.addEventListener('click', (e) => {
            document.querySelectorAll('.nav-tab').forEach(el => el.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
            e.target.classList.add('active');
            const tabId = e.target.getAttribute('data-tab');
            document.getElementById('tab-' + tabId).classList.add('active');
            const titles = { overview: 'Dashboard Overview', records: 'Records' };
            document.getElementById('page-title').textContent = titles[tabId] || 'Dashboard';
            if (tabId === 'overview') loadDashboard();
            if (tabId === 'records') loadRecords();
        });
    });

    // Modal logic
    const modal = document.getElementById('modal');
    document.getElementById('add-btn').addEventListener('click', () => {
        document.getElementById('record-form').reset();
        document.getElementById('f-id').readOnly = false;
        document.getElementById('modal-title').textContent = 'Add Disaster';
        modal.classList.add('active');
    });
    document.getElementById('cancel-btn').addEventListener('click', () => {
        modal.classList.remove('active');
    });

    // Search
    document.getElementById('search-input').addEventListener('input', (e) => {
        loadRecords(e.target.value);
    });

    // Form Submission (Add/Edit)
    document.getElementById('record-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        const event_id = document.getElementById('f-id').value;
        const payload = {
            event_id,
            name:       document.getElementById('f-name').value,
            type:       document.getElementById('f-type').value,
            region:     document.getElementById('f-region').value,
            country:    document.getElementById('f-country').value,
            date:       document.getElementById('f-date').value,
            magnitude:  document.getElementById('f-mag').value,
            casualties: document.getElementById('f-cas').value,
            status:     document.getElementById('f-status').value
        };
        const isEdit = document.getElementById('f-id').readOnly;
        const url    = isEdit ? `/api/disasters/${event_id}` : '/api/disasters';
        const method = isEdit ? 'PUT' : 'POST';
        try {
            const res = await fetch(url, {
                method, headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            const data = await res.json();
            if (data.success) { modal.classList.remove('active'); loadDashboard(); loadRecords(); }
            else { alert(data.message || 'Operation failed'); }
        } catch (err) { alert('Server error'); }
    });

    function showLogin() {
        document.getElementById('dashboard-view').classList.remove('active');
        document.getElementById('login-view').classList.add('active');
    }

    function showDashboard() {
        document.getElementById('login-view').classList.remove('active');
        document.getElementById('dashboard-view').classList.add('active');
        loadDashboard();
        loadRecords();
    }

    async function loadDashboard() {
        const res = await fetch('/api/dashboard');
        if (res.status === 401) return showLogin();
        const data = await res.json();
        document.getElementById('stat-total').textContent  = data.total;
        document.getElementById('stat-active').textContent = data.active;
        if (data.highest_magnitude) {
            document.getElementById('stat-mag').textContent      = data.highest_magnitude.magnitude;
            document.getElementById('stat-mag-name').textContent = data.highest_magnitude.name;
        } else {
            document.getElementById('stat-mag').textContent      = '-';
            document.getElementById('stat-mag-name').textContent = '-';
        }
        document.getElementById('stat-region').textContent = data.most_affected_region;

        const tbody = document.getElementById('deadliest-tbody');
        tbody.innerHTML = '';
        data.deadliest.forEach(d => {
            if (!d) return;
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${d.name}</td><td>${d.type}</td><td>${d.date}</td>
                <td>${d.casualties.toLocaleString()}</td>
                <td><span class="status-badge ${d.status === 'Active' ? 'status-active' : 'status-inactive'}">${d.status}</span></td>`;
            tbody.appendChild(tr);
        });
        renderBarChart(data.deadliest);
    }

    function renderBarChart(deadliest) {
        const ctx = document.getElementById('casualties-chart');
        if (!ctx) return;
        const typeMap = {};
        deadliest.forEach(d => { if (!d) return; typeMap[d.type] = (typeMap[d.type] || 0) + d.casualties; });
        const labels = Object.keys(typeMap);
        const values = Object.values(typeMap);
        const colors = ['#72baff','#6ce0a3','#ffb347','#b794f4','#f6ad55'];
        if (chartInstance) { chartInstance.destroy(); chartInstance = null; }
        chartInstance = new Chart(ctx, {
            type: 'bar',
            data: { labels, datasets: [{ label: 'Total Casualties', data: values,
                backgroundColor: colors.slice(0, labels.length), borderRadius: 10,
                maxBarThickness: 90, borderSkipped: false }] },
            options: { responsive: true, maintainAspectRatio: false,
                plugins: { legend: { display: false },
                    tooltip: { callbacks: { label: ctx => ` ${ctx.parsed.y.toLocaleString()} casualties` } } },
                scales: {
                    x: { ticks: { color: '#9fb0cf', font: { family: 'Inter' } }, grid: { color: 'rgba(255,255,255,0.04)' } },
                    y: { ticks: { color: '#9fb0cf', font: { family: 'Inter' }, callback: v => v.toLocaleString() }, grid: { color: 'rgba(255,255,255,0.05)' } }
                }
            }
        });
    }

    async function loadRecords(search = '') {
        const url = search ? `/api/disasters?search=${encodeURIComponent(search)}` : '/api/disasters';
        const res = await fetch(url);
        if (res.status === 401) return showLogin();
        const data = await res.json();
        const tbody = document.getElementById('records-tbody');
        tbody.innerHTML = '';
        if (!data.length) {
            document.getElementById('empty-state').hidden = false;
        } else {
            document.getElementById('empty-state').hidden = true;
            data.forEach(d => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td>${d.event_id}</td><td>${d.name}</td><td>${d.type}</td>
                    <td>${d.region}</td><td>${d.magnitude}</td>
                    <td><span class="status-badge ${d.status === 'Active' ? 'status-active' : 'status-inactive'}">${d.status}</span></td>
                    <td><button class="action-btn edit" data-id="${d.event_id}">Edit</button>
                        <button class="action-btn delete" data-id="${d.event_id}">Delete</button></td>`;
                tbody.appendChild(tr);
            });
        }
        document.getElementById('rec-total').textContent = data.length;
        document.getElementById('rec-active').textContent = data.filter(r => r.status === 'Active').length;
        document.getElementById('rec-inactive').textContent = data.filter(r => r.status === 'Inactive').length;
        document.querySelectorAll('.action-btn.edit').forEach(btn => {
            btn.addEventListener('click', e => editRecord(e.target.getAttribute('data-id'), data));
        });
        document.querySelectorAll('.action-btn.delete').forEach(btn => {
            btn.addEventListener('click', e => deleteRecord(e.target.getAttribute('data-id')));
        });
    }

    function editRecord(id, dataList) {
        const record = dataList.find(d => d.event_id === id);
        if (!record) return;
        document.getElementById('f-id').value = record.event_id;
        document.getElementById('f-id').readOnly = true;
        document.getElementById('f-name').value = record.name;
        document.getElementById('f-type').value = record.type;
        document.getElementById('f-region').value = record.region;
        document.getElementById('f-country').value = record.country;
        document.getElementById('f-date').value = record.date;
        document.getElementById('f-mag').value = record.magnitude;
        document.getElementById('f-cas').value = record.casualties;
        document.getElementById('f-status').value = record.status;
        document.getElementById('modal-title').textContent = 'Edit Disaster';
        modal.classList.add('active');
    }

    async function deleteRecord(id) {
        if (!confirm(`Are you sure you want to delete ${id}?`)) return;
        try {
            const res = await fetch(`/api/disasters/${id}`, { method: 'DELETE' });
            const data = await res.json();
            if (data.success) { loadDashboard(); loadRecords(document.getElementById('search-input').value); }
            else { alert(data.message || 'Delete failed'); }
        } catch (err) { alert('Server error'); }
    }
});
```

---

## Frontend Code (continued)

### static/index.css — Full Stylesheet

See [index.css](static/index.css) in the project directory for the complete 479-line stylesheet. Key design tokens:

| Variable    | Value                          | Purpose           |
|-------------|--------------------------------|--------------------|
| `--bg`      | `#060b1a`                      | Page background    |
| `--panel`   | `rgba(14, 23, 46, 0.88)`      | Card/panel fill    |
| `--border`  | `rgba(109, 143, 201, 0.16)`   | Subtle borders     |
| `--text`    | `#eef4ff`                      | Primary text       |
| `--blue`    | `#56a8ff`                      | Accent color       |
| `--green`   | `#25d18a`                      | Success/inactive   |
| `--yellow`  | `#f7b941`                      | Warning/active     |
| `--danger`  | `#ff5b73`                      | Error states       |

### templates/index.html — Full Template

See [index.html](templates/index.html) in the project directory for the complete 470-line template including the Three.js planet animation and cloud layer.

---

## Running the Application

```bash
# 1. Navigate to project
cd sentinel

# 2. Create virtual environment
python3 -m venv venv
source venv/bin/activate

# 3. Install dependencies
pip install flask

# 4. Run the server
python app.py

# 5. Open in browser
open http://127.0.0.1:5000
```

**Default credentials:** `admin` / `admin123`
