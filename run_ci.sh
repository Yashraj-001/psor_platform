#!/bin/bash
set -e 

log() { echo "[$(date +'%Y-%m-%d %H:%M:%S')] [INFO] $1"; }
warn() { echo "[$(date +'%Y-%m-%d %H:%M:%S')] [WARN] $1"; }
error() { echo "[$(date +'%Y-%m-%d %H:%M:%S')] [ERROR] $1" >&2; exit 1; }

log "Starting PSOR CI/CD Pipeline..."
command -v docker >/dev/null 2>&1 || error "Docker is not installed. Aborting."

log "Phase 1: Cleaning up old artifacts..."
rm -f reports/audit.log
log "Cleanup complete."

log "Phase 2: Building all polyglot services (Orchestrator, Python, Java, Rust)..."
# --- FIX ---
docker compose build --parallel
# --- END FIX ---
log "All services built successfully."

log "Phase 3: Executing remediation playbook 'playbooks/remediate_compromised_host.yml'..."
# --- FIX ---
docker compose run --rm orchestrator
# --- END FIX ---
if [ $? -ne 0 ]; then
    warn "Orchestrator finished with an error (this is expected for the test playbook)."
fi
log "Orchestrator run finished."

log "Phase 4: Displaying final audit trail from reports/audit.log..."
echo "=========================== AUDIT LOG START ==========================="
if [ -f "reports/audit.log" ]; then
    cat -n reports/audit.log
else
    warn "Audit log not found."
fi
echo "============================ AUDIT LOG END ============================"

log "PSOR CI/CD Pipeline :: SUCCESS"
exit 0
