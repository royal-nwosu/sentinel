from flask import Flask, render_template, request, jsonify, session
import os
from auth import authenticate
from manager import SystemManager

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', os.urandom(24))

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
    
    # Serialize complex objects
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
