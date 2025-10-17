import yaml
import docker
import sys
import json
import logging
import random # Needed for conceptual Jira ticket ID
from datetime import datetime

# --- Logging Setup (same as before) ---
def setup_logging():
    log_formatter = logging.Formatter('%(asctime)s [%(levelname)-5.5s]  %(message)s')
    root_logger = logging.getLogger()
    if root_logger.hasHandlers():
        root_logger.handlers.clear()
    root_logger.setLevel(logging.INFO)
    file_handler = logging.FileHandler("reports/audit.log", mode='a') # Append mode
    file_handler.setFormatter(log_formatter)
    root_logger.addHandler(file_handler)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(log_formatter)
    root_logger.addHandler(console_handler)

class Orchestrator:
    def __init__(self, playbook_path):
        try:
            self.docker_client = docker.from_env()
        except Exception as e:
             logging.error(f"Failed to connect to Docker: {e}. Is Docker running and accessible?")
             sys.exit(1)
        self.playbook = self._load_playbook(playbook_path)
        self.safety_policies = {p['name']: p for p in self.playbook.get('safety_policies', [])}
        logging.info(f"Successfully loaded playbook: {self.playbook['name']}")

    def _load_playbook(self, path):
        try:
            with open(path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logging.error(f"Failed to load or parse playbook {path}: {e}")
            sys.exit(1)

    def _check_safety_policies(self, plugin_name, params):
        if "block-ip" in plugin_name:
            policy = self.safety_policies.get("corporate_ip_check")
            if policy and params.get("ip_address") in policy.get("targets", []):
                logging.warning(f"[SAFETY_CHECK_VIOLATION] Action BLOCKED. Attempted to block corporate IP: {params['ip_address']}")
                return False
        if "isolate-endpoint" in plugin_name:
            policy = self.safety_policies.get("critical_asset_check")
            if policy and params.get("endpoint_id") in policy.get("targets", []):
                logging.warning(f"[SAFETY_CHECK_VIOLATION] Action BLOCKED. Attempted to isolate critical asset: {params['endpoint_id']}")
                return False
        logging.info("[SAFETY_CHECK_PASSED] Action is approved for execution.")
        return True

    def _execute_rollback(self, failed_step_name, failed_plugin, failed_params):
        logging.critical(f"[ROLLBACK_PROCEDURE] Attempting rollback for failed step: '{failed_step_name}'")
        
        rollback_plugin = None
        rollback_params = {}

        # --- Define Rollback Mappings ---
        # In production, this mapping might be more sophisticated or part of the playbook definition
        rollback_map = {
            "psor_platform_plugin-python-revoke-key": None, # No easy rollback
            "psor_platform_plugin-java-block-ip": "psor_platform_plugin-java-unblock-ip", # Hypothetical plugin
            "psor_platform_plugin-rust-isolate-endpoint": "psor_platform_plugin-rust-unisolate-endpoint" # Hypothetical plugin
        }
        
        rollback_plugin = rollback_map.get(failed_plugin)

        if not rollback_plugin:
            logging.warning(f"No automatic rollback plugin defined for: {failed_plugin}. Manual intervention likely required.")
            return

        # Prepare parameters (often the same as the failed step)
        rollback_params = failed_params
        if not all(rollback_params.values()):
             logging.error(f"Could not determine valid rollback parameters for {failed_plugin} with params {failed_params}")
             return
             
        logging.info(f"Initiating rollback plugin '{rollback_plugin}' with params: {rollback_params}")
        
        # --- Execute the Rollback Plugin ---
        try:
           command = [f"{k}={v}" for k, v in rollback_params.items()]
           # NOTE: We assume rollback plugins exist but haven't built them. This call will fail if they don't exist.
           # To test this flow fully, you would need to build e.g., 'plugin-java-unblock-ip'
           container = self.docker_client.containers.run(rollback_plugin, command, detach=False, remove=True, network_mode='host')
           output = container.decode('utf-8').strip()
           logging.info(f"[ROLLBACK_OUTPUT] {output}")
           logging.info(f"Rollback for step '{failed_step_name}' completed.")
        except docker.errors.ImageNotFound:
             logging.error(f"Rollback FAILED: Rollback plugin image '{rollback_plugin}' not found. Build the rollback plugin.")
        except docker.errors.ContainerError as e_rollback:
             error_output = e_rollback.stderr.decode('utf-8').strip() if e_rollback.stderr else "No stderr."
             logging.error(f"Rollback plugin '{rollback_plugin}' FAILED with exit code {e_rollback.exit_status}. Error: {error_output}")
        except Exception as e_rollback:
           logging.error(f"Rollback plugin '{rollback_plugin}' FAILED with unexpected error: {e_rollback}")
        # --- End Rollback Execution ---


    def run_playbook(self):
        logging.info("Starting playbook execution...")
        executed_steps_history = [] 

        for i, step in enumerate(self.playbook['steps']):
            step_name = step['name']
            plugin_image = step['plugin']
            params = step.get('parameters', {})
            
            logging.info(f"--- Starting Step {i+1}: {step_name} ---")

            if not self._check_safety_policies(plugin_image, params):
                executed_steps_history.append({'step': step, 'status': 'skipped_policy'})
                continue 

            command = [f"{k}={v}" for k, v in params.items()]

            try:
                logging.info(f"Executing plugin '{plugin_image}' with params: {command}")
                # Use host network mode for plugins that might need to interact with local network/firewall
                container = self.docker_client.containers.run(
                    image=plugin_image, command=command, detach=False, remove=True, network_mode='host') 
                output = container.decode('utf-8').strip()
                # Attempt to parse as JSON, otherwise treat as raw string
                try:
                    result = json.loads(output)
                    logging.info(f"[PLUGIN_OUTPUT] {result}")
                    executed_steps_history.append({'step': step, 'status': 'success', 'output': result})
                except json.JSONDecodeError:
                    logging.info(f"[PLUGIN_RAW_OUTPUT] {output}") # Log raw if not JSON
                    executed_steps_history.append({'step': step, 'status': 'success', 'output': output})

                logging.info(f"Step '{step_name}' completed successfully.")

            except docker.errors.ContainerError as e:
                error_output = e.stderr.decode('utf-8').strip() if e.stderr else "No stderr."
                logging.error(f"Step '{step_name}' FAILED with exit code {e.exit_status}. Error: {error_output}")
                executed_steps_history.append({'step': step, 'status': 'failed', 'error': error_output})
                self._execute_rollback(step_name, plugin_image, params)
                if step.get("on_failure") == "stop":
                    logging.error("Playbook execution halted due to 'on_failure: stop' policy.")
                    sys.exit(1)
            
            except docker.errors.ImageNotFound:
                 logging.error(f"Step '{step_name}' FAILED: Plugin image '{plugin_image}' not found. Ensure it is built.")
                 executed_steps_history.append({'step': step, 'status': 'failed', 'error': f"Image not found: {plugin_image}"})
                 # No rollback possible if plugin image doesn't exist
                 if step.get("on_failure") == "stop":
                     sys.exit(1)

            except Exception as e:
                logging.exception(f"An unexpected error occurred while running plugin '{plugin_image}': {e}") # Use logging.exception for full traceback
                executed_steps_history.append({'step': step, 'status': 'error', 'error': str(e)})
                # Attempt rollback even on unexpected errors
                self._execute_rollback(step_name, plugin_image, params)
                if step.get("on_failure") == "stop":
                    sys.exit(1)

        logging.info("--- Playbook execution finished. ---")


if __name__ == "__main__":
    setup_logging()
    # Allow running without args for testing, default to specific playbook
    playbook_arg = sys.argv[1] if len(sys.argv) > 1 else "playbooks/remediate_compromised_host.yml" 
    
    orchestrator = Orchestrator(playbook_arg)
    orchestrator.run_playbook()
