from flask import Flask, request, jsonify
import subprocess
import json
import logging
import os
import tempfile
import uuid
import yaml

app = Flask(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

PLAYBOOK_MAPPING = {
    "AWS Credential Leak Detected": "playbooks/remediate_compromised_host.yml",
    "Malicious C2 Communication Detected": "playbooks/remediate_compromised_host.yml",
}

def extract_params(alert_data):
    params = {}
    aws_key = alert_data.get("detail", {}).get("requestParameters", {}).get("accessKeyId")
    if aws_key: params["key_id"] = aws_key
    src_ip = alert_data.get("source_ip")
    dest_ip = alert_data.get("destination_ip")
    if dest_ip and not dest_ip.startswith(("10.", "192.168.", "172.16.")): params["ip_address"] = dest_ip
    elif src_ip: params["ip_address"] = src_ip
    hostname = alert_data.get("hostname") or alert_data.get("computerName")
    if hostname: params["endpoint_id"] = hostname
    return params

@app.route('/webhook', methods=['POST'])
def siem_webhook():
    try:
        alert_data = request.json
        if not alert_data:
            logging.warning("Received empty request body.")
            return jsonify({"status": "error", "message": "Empty request body"}), 400

        logging.info(f"Received alert: {json.dumps(alert_data, indent=2)}")
        alert_name = alert_data.get("rule_name") or alert_data.get("rule", {}).get("name")
        playbook_path = PLAYBOOK_MAPPING.get(alert_name)

        if not playbook_path:
            logging.info(f"No playbook mapped for alert: '{alert_name}'. Ignoring.")
            return jsonify({"status": "ignored", "message": "No playbook mapping found"}), 200

        extracted_params = extract_params(alert_data)
        logging.info(f"Extracted parameters: {extracted_params}")
        logging.info(f"Mapped to playbook: {playbook_path}")

        try:
             project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
             base_playbook_path = os.path.join(project_root, playbook_path)
             with open(base_playbook_path, 'r') as f_base:
                 temp_playbook_data = yaml.safe_load(f_base)

             if 'steps' in temp_playbook_data:
                 for step in temp_playbook_data['steps']:
                     if 'parameters' in step:
                         for key, value in extracted_params.items():
                              if key in step['parameters']:
                                   step['parameters'][key] = value

             temp_playbook_name = f"runtime_playbook_{uuid.uuid4()}.yml"
             temp_playbook_path_host = os.path.join(project_root, "playbooks", temp_playbook_name)
             temp_playbook_path_container = f"/app/playbooks/{temp_playbook_name}" 

             with open(temp_playbook_path_host, 'w') as f_temp:
                 yaml.dump(temp_playbook_data, f_temp)
             
             logging.info(f"Generated temporary playbook: {temp_playbook_name}")

             # --- FIX ---
             # Use modern 'docker compose'
             orchestrator_command = [
                 "docker", "compose", 
                 "-f", "../docker-compose.yml", 
                 "run", # Use run, not exec, as orchestrator isn't running daemonized
                 "--rm",
                 "-T",   
                 "orchestrator", 
                 "python3", "orchestrator.py", 
                 temp_playbook_path_container 
             ]
             # --- END FIX ---
             
             logging.info(f"Executing command: {' '.join(orchestrator_command)}")
             # This is now 100% real code, it will execute the command
             result = subprocess.run(orchestrator_command, cwd=project_root, capture_output=True, text=True)
             
             # Clean up temp playbook file *after* execution
             try:
                 os.remove(temp_playbook_path_host)
                 logging.info(f"Removed temporary playbook: {temp_playbook_name}")
             except OSError as e_rm:
                 logging.warning(f"Failed to remove temporary playbook: {e_rm}")

             if result.returncode == 0:
                 logging.info(f"Orchestrator finished successfully via adapter. Output:\n{result.stdout}")
                 return jsonify({"status": "success", "message": f"Triggered and completed playbook {playbook_path}"}), 200
             else:
                 logging.error(f"Orchestrator failed via adapter. Return Code: {result.returncode}\nStderr:\n{result.stderr}\nStdout:\n{result.stdout}")
                 return jsonify({"status": "error", "message": f"Orchestrator failed (Code: {result.returncode})"}), 500

        except Exception as e_inner:
             logging.exception("Error during playbook generation or execution:")
             return jsonify({"status": "error", "message": "Internal error during trigger"}), 500

    except Exception as e:
        logging.exception("Error processing webhook:")
        return jsonify({"status": "error", "message": "Internal server error"}), 500

if __name__ == '__main__':
    os.makedirs(os.path.join(os.path.dirname(__file__), "..", "playbooks"), exist_ok=True) 
    logging.info("Starting SIEM Webhook Listener on port 5001...")
    app.run(host='0.0.0.0', port=5001, debug=False) 
