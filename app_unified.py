from flask import Flask, render_template, jsonify, request, send_from_directory
from flask_socketio import SocketIO, emit
import subprocess
import os
import threading
import pty 
import logging
import yaml
import json

def setup_logging():
    log_formatter = logging.Formatter('%(asctime)s [%(levelname)-5.5s]  %(message)s')
    root_logger = logging.getLogger()
    if root_logger.hasHandlers(): root_logger.handlers.clear()
    root_logger.setLevel(logging.INFO)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(log_formatter)
    root_logger.addHandler(console_handler)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key!' 
socketio = SocketIO(app, async_mode='threading', ws_server='simple-websocket') 

pipeline_running = False
pipeline_thread = None

def run_pipeline_thread(playbook_file="playbooks/remediate_compromised_host.yml"):
    global pipeline_running
    process = None 
    master_fd = -1 
    try:
        socketio.emit('status_update', {'status': f'Building & Running Playbook: {os.path.basename(playbook_file)}...'})
        master_fd, slave_fd = pty.openpty()
        
        # --- FIX ---
        command = [
            'docker', 'compose', # Use modern 'docker compose'
            'run', '--rm', 
            'orchestrator', 
            'python3', 'orchestrator.py', 
            playbook_file
        ]
        # --- END FIX ---
        
        process = subprocess.Popen(
            command, 
            stdout=slave_fd, stderr=slave_fd, text=True, bufsize=1,
            cwd=os.path.dirname(os.path.abspath(__file__))
        )
        os.close(slave_fd)

        with open(master_fd, 'r') as stdout_reader:
            while True:
                try:
                    line = stdout_reader.readline()
                    if not line: break 
                    socketio.emit('pipeline_log', {'log': line.strip()})
                    socketio.sleep(0.01)
                except OSError as e:
                    if e.errno == 5: 
                        socketio.emit('pipeline_log', {'log': f'[INFO] End of stream detected (OSError 5).'})
                        break 
                    else: raise 

        return_code = process.wait() 
        if return_code == 0:
            socketio.emit('status_update', {'status': 'Playbook Finished Successfully ✅'})
        else:
            socketio.emit('status_update', {'status': f'Playbook Finished with Error (Code: {return_code}) ❌'})
    except Exception as e:
        socketio.emit('status_update', {'status': f'Error running playbook: {str(e)} ❌'})
        socketio.emit('pipeline_log', {'log': f'BACKEND ERROR: {str(e)}'})
    finally:
        pipeline_running = False
        if master_fd != -1:
            try: os.close(master_fd)
            except OSError: pass

@app.route('/')
def index():
    return render_template('unified_ui.html') 

@app.route('/run_playbook', methods=['POST'])
def run_playbook_endpoint():
    global pipeline_running, pipeline_thread
    if pipeline_running:
        return jsonify({"status": "error", "message": "Pipeline already running."}), 409
    data = request.json
    playbook_to_run = data.get('playbook', 'playbooks/remediate_compromised_host.yml') 
    if not os.path.exists(playbook_to_run):
         return jsonify({"status": "error", "message": f"Playbook file not found: {playbook_to_run}"}), 404
    pipeline_running = True
    socketio.emit('status_update', {'status': 'Playbook run requested...'})
    socketio.emit('clear_logs', {}) 
    pipeline_thread = threading.Thread(target=run_pipeline_thread, args=(playbook_to_run,))
    pipeline_thread.start()
    return jsonify({"status": "success", "message": "Playbook run started."}), 202

SAFETY_POLICIES = {
    "critical_asset_check": {"type": "do_not_isolate", "targets": ["endpoint-db-01", "endpoint-auth-svc"], "message": "Endpoint is a critical production asset."},
    "corporate_ip_check": {"type": "do_not_block", "targets": ["8.8.8.8", "1.1.1.1", "208.67.222.222"], "message": "IP is a critical infrastructure service (e.g., public DNS)."}
}

@app.route('/validate_playbook', methods=['POST'])
def validate_playbook_endpoint():
    playbook_yaml = request.data.decode('utf-8')
    results = []
    playbook = None
    try:
        playbook = yaml.safe_load(playbook_yaml)
        results.append({'type': 'success', 'title': 'YAML Syntax OK', 'message': 'Playbook parsed successfully.'})
    except Exception as e:
        results.append({'type': 'error', 'title': 'YAML Syntax Error', 'message': str(e)})
        return jsonify(results)
    if not playbook or not isinstance(playbook, dict) or 'steps' not in playbook:
        results.append({'type': 'error', 'title': 'Invalid Playbook Structure', 'message': 'Must be a YAML object with a "steps" list.'})
        return jsonify(results)
    results.append({'type': 'info', 'title': 'Starting Policy Validation', 'message': f"Found {len(playbook['steps'])} steps."})
    for index, step in enumerate(playbook['steps']):
        step_name = step.get('name', f"Unnamed Step {index + 1}")
        plugin = step.get('plugin', '')
        params = step.get('parameters', {})
        is_safe = True
        if plugin and "isolate-endpoint" in plugin:
            policy = SAFETY_POLICIES.get("critical_asset_check")
            target = params.get("endpoint_id")
            if policy and target and target in policy.get("targets", []):
                results.append({'type': 'error', 'title': f'Step "{step_name}" VIOLATES policy!', 'message': f'[{policy.get("type")}] {policy.get("message")} Target: {target}'})
                is_safe = False
        if plugin and "block-ip" in plugin:
            policy = SAFETY_POLICIES.get("corporate_ip_check")
            target = params.get("ip_address")
            if policy and target and target in policy.get("targets", []):
                results.append({'type': 'error', 'title': f'Step "{step_name}" VIOLATES policy!', 'message': f'[{policy.get("type")}] {policy.get("message")} Target: {target}'})
                is_safe = False
        if is_safe:
            results.append({'type': 'success', 'title': f'Step "{step_name}" PASSED', 'message': 'No safety policy violations found.'})
    return jsonify(results)

@app.route('/audit_log')
def get_audit_log():
    log_path = os.path.join(os.path.dirname(__file__), 'reports', 'audit.log')
    if os.path.exists(log_path):
        return send_from_directory('reports', 'audit.log', mimetype='text/plain')
    else:
        return "Audit log file not found.", 404
        
@app.route('/playbooks_list')
def get_playbooks_list():
    playbook_dir = os.path.join(os.path.dirname(__file__), 'playbooks')
    try:
        files = [f for f in os.listdir(playbook_dir) if os.path.isfile(os.path.join(playbook_dir, f)) and f.endswith(('.yml', '.yaml'))]
        return jsonify([os.path.join('playbooks', f) for f in files])
    except FileNotFoundError:
        return jsonify([])

if __name__ == '__main__':
    setup_logging()
    print("Starting Unified PSOR UI Server on http://localhost:5000")
    socketio.run(app, host='0.0.0.0', port=5000, debug=False, allow_unsafe_werkzeug=True) 
