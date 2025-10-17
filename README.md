# Project 10: Polyglot Automated Security Orchestration & Remediation (PSOR)

**Status:** Core Engine & UI Complete | **Build:** Passing

An advanced, playbook-driven orchestration engine designed to automate security incident remediation across diverse (polyglot) toolchains. PSOR ensures remediation is safe, auditable, and fast by executing sandboxed plugins based on YAML playbooks, all while enforcing a built-in safety policy engine.

---

## 🚀 Core Features

**Playbook-Driven Engine:** Uses simple YAML files to define complex remediation workflows.

**Polyglot Plugin Architecture:** Supports remediation plugins written in Python, Java, Rust, and JavaScript (Node.js), each with its own SDK.

**Secure Sandboxing:** All plugins are executed in isolated, minimal Docker containers (scratch image used for Rust) to prevent lateral movement and ensure safety.

**Policy-as-Code Safety Engine:** A built-in validator in the orchestrator checks every action against a set of `safety_policies` (e.g., “do-not-block” critical IPs) before execution.

**Real-time UI & Pipeline Viewer:** A comprehensive web dashboard (built with Flask & SocketIO) to:

* Select and run playbooks in real-time
* Stream the entire build and execution log live to the browser
* Validate playbooks against safety policies
* View historical audit logs

**Complete Audit Trail:** Generates a detailed `audit.log` for every action, decision, and outcome, ensuring 100% auditable remediation.

**Automated CI/CD:** A production-grade GitHub Actions workflow automatically builds, tests, and validates the entire polyglot platform on every push and pull request.

**Rollback Framework:** The orchestrator is designed to trigger corresponding rollback plugins (e.g., `unblock-ip`) upon failure.

**Integration Adapters:** Includes a real SIEM webhook listener that can receive alerts and trigger playbook runs.

---

## 🛠️ Tech Stack

**Orchestration:** Python, Docker SDK
**Web Backend & UI:** Flask, Flask-SocketIO, HTML/JS, ansi_up

**Plugins & SDKs:**

* Python 3 (with Jira library)
* Java 17 (Maven)
* Rust (Cargo, with static musl builds)
* Node.js 18 (npm)

**CI/CD:** GitHub Actions, Docker Compose (v2)

---

## 📂 Project Structure

```bash
psor_platform/
├── .github/workflows/
│   └── main.yml           # Production CI/CD Pipeline (GitHub Actions)
├── adapters/
│   ├── requirements.txt   # SIEM Adapter Python dependencies
│   └── siem_listener.py   # Real SIEM webhook listener (Flask app)
├── app_unified.py         # Main backend for the Unified Web UI (Flask + SocketIO)
├── docker-compose.yml     # Defines all services, plugins, and build contexts
├── orchestrator/
│   ├── Dockerfile
│   └── orchestrator.py    # The core Python orchestration engine
├── playbooks/
│   └── remediate_compromised_host.yml # The main test playbook
├── plugins/
│   ├── java-sdk/
│   │   ├── block-ip-address/    # Java "block-ip" plugin
│   │   ├── psor-sdk-lib/        # Java SDK library
│   │   └── unblock-ip-address/  # Java "unblock-ip" rollback plugin
│   ├── js-sdk/
│   │   ├── log-message/         # Node.js "log-message" plugin
│   │   └── psor-sdk-lib/        # JavaScript (Node.js) SDK library
│   ├── python-sdk/
│   │   ├── psor_sdk.py          # Python SDK library
│   │   └── revoke-iam-key/      # Python "revoke-iam-key" plugin (with Jira)
│   └── rust-sdk/
│       ├── isolate-endpoint/    # Rust "isolate-endpoint" plugin
│       ├── psor-sdk-lib/        # Rust SDK library (crate)
│       └── unisolate-endpoint/  # Rust "unisolate-endpoint" rollback plugin
├── reports/
│   └── audit.log            # The main audit trail file (generated on run)
├── requirements.txt       # Main UI Server Python dependencies
├── run_ci.sh              # Local CI/CD simulation script (uses docker compose)
└── templates/
    └── unified_ui.html    # The main single-page-application (SPA) frontend
```

---

## 🏁 How to Run

### 1️⃣ Build All Services

First, build all the container images for the orchestrator and all polyglot plugins.

```bash
docker compose build
```

---

### 2️⃣ Run via the Real-time Web UI (Recommended)

This is the best way to interact with the project.

**Install UI Dependencies:**

```bash
pip install -r requirements.txt
```

**Run the Web Server:**

```bash
python3 app_unified.py
```

**Open the Dashboard:**
Navigate to 👉 [http://localhost:5000](http://localhost:5000)

* **Pipeline Runner Tab:** Select a playbook and click **Run Selected Playbook** to see the entire build and orchestration stream live.
* **Playbook Validator Tab:** Paste any playbook YAML to check it against the safety engine.
* **Audit Log History Tab:** Click **Refresh** to view the latest audit logs.

---

### 3️⃣ Run via the Local CI/CD Script

This simulates the CI process and runs the default playbook — perfect for quick CLI testing.

**Make script executable:**

```bash
chmod +x run_ci.sh
```

**Run the script:**

```bash
./run_ci.sh
```

This will build all images (if not already built) and execute `remediate_compromised_host.yml`, printing the full audit log at the end.

---

## 🔌 Testing Integration Adapters

### Real SIEM Webhook Listener

**Install Adapter Dependencies:**

```bash
pip install -r adapters/requirements.txt
```

**Run the Adapter (in a separate terminal):**

```bash
python3 adapters/siem_listener.py
```

The adapter will start listening on **port 5001**.

**Simulate a SIEM Alert:**

```bash
curl -X POST -H "Content-Type: application/json" \
     -d '{"rule_name": "Malicious C2 Communication Detected", "destination_ip": "123.123.123.123", "hostname": "finance-pc-05"}' \
     http://localhost:5001/webhook
```

You will see the full orchestrator run logs appear in the `siem_listener.py` terminal output.
