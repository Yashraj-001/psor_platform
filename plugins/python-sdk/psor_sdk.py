import sys
import json
import random
import logging
import os  # <--- THIS IS THE FIX

# --- Setup basic logging for SDK functions ---
sdk_logger = logging.getLogger("PSOR_SDK")
if not sdk_logger.hasHandlers():
    sdk_handler = logging.StreamHandler(sys.stderr) 
    sdk_formatter = logging.Formatter('%(asctime)s [SDK:%(levelname)s] %(message)s')
    sdk_handler.setFormatter(sdk_formatter)
    sdk_logger.addHandler(sdk_handler)
    sdk_logger.setLevel(logging.INFO)


def parse_args():
    """Parses key=value args into a dictionary."""
    params = {}
    for arg in sys.argv[1:]:
        try:
            key, value = arg.split('=', 1)
            params[key] = value
        except ValueError:
            sdk_logger.warning(f"Malformed argument ignored: {arg}")
    return params

def success_response(message, details=None):
    """Prints JSON success response and exits 0."""
    response = {"status": "success", "message": message}
    if details:
        response["details"] = details
    print(json.dumps(response))
    sys.exit(0)

def error_response(message, exit_code=1, stderr_message=None):
    """Prints JSON error response, logs to stderr, and exits non-zero."""
    response = {"status": "error", "message": message}
    print(json.dumps(response))
    if stderr_message:
        sdk_logger.error(stderr_message) 
    sys.exit(exit_code)

# --- Real Jira Library Integration (Conceptual Connection) ---
try:
    from jira import JIRA
    # --- CONFIGURATION NEEDED ---
    JIRA_SERVER = os.environ.get("JIRA_SERVER", "https://your-jira-instance.atlassian.net") 
    JIRA_USERNAME = os.environ.get("JIRA_USERNAME", "your-email@example.com")
    JIRA_API_TOKEN = os.environ.get("JIRA_API_TOKEN", "YOUR_API_TOKEN") 
    # --- END CONFIGURATION ---
    
    jira_options = {'server': JIRA_SERVER}
    
    _jira_client = None
    def get_jira_client():
        global _jira_client
        if _jira_client is None:
             try:
                 sdk_logger.info(f"Attempting Jira connection to {JIRA_SERVER}...")
                 _jira_client = JIRA(options=jira_options, basic_auth=(JIRA_USERNAME, JIRA_API_TOKEN))
                 sdk_logger.info("Jira client initialized (connection test deferred until first API call).")
             except Exception as e:
                 sdk_logger.error(f"Failed to initialize Jira client: {e}")
                 _jira_client = "FAILED"
        return _jira_client if _jira_client != "FAILED" else None

except ImportError:
    sdk_logger.warning("Jira library not found. Jira integration will be simulated.")
    JIRA = None 
    def get_jira_client(): return None


def create_jira_ticket(summary, description, project_key="SEC", issue_type="Task"):
    """
    Creates a Jira ticket using the real library structure.
    """
    jira = get_jira_client()

    if jira:
        try:
            issue_dict = {
                'project': {'key': project_key},
                'summary': summary,
                'description': description,
                'issuetype': {'name': issue_type},
            }
            sdk_logger.info(f"Attempting to create Jira issue: {issue_dict}")
            new_issue = jira.create_issue(fields=issue_dict)
            sdk_logger.info(f"Successfully created Jira ticket: {new_issue.key}")
            return new_issue.key
        except Exception as e:
            sdk_logger.error(f"Failed to create Jira ticket: {e}. Falling back to simulation.")
    
    # --- Simulation Fallback ---
    ticket_id = f"{project_key}-{random.randint(1000, 9999)}" 
    log_message = (
        f"*** SIMULATION: Would create Jira ticket {ticket_id} in project {project_key} "
        f"with summary='{summary}' ***"
    )
    sdk_logger.warning(log_message)
    return ticket_id
