#!/bin/bash

# A professional-grade CI script for the PSOR platform.
# Features:
# - Strict error checking (set -e).
# - Verbose logging with timestamps.
# - Separation of build, test, and execution phases.
# - Dynamic check for required tools (docker, jq).

set -e # Exit immediately if a command exits with a non-zero status.

# --- Helper Functions for Logging ---
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] [INFO] $1"
}

warn() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] [WARN] $1"
}

error() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] [ERROR] $1" >&2
    exit 1
}

# --- Pre-flight Checks ---
log "Starting PSOR CI/CD Pipeline..."
command -v docker >/dev/null 2>&1 || error "Docker is not installed. Aborting."
command -v docker-compose >/dev/null 2>&1 || error "Docker Compose is not installed. Aborting."

# --- Phase 1: Cleanup ---
log "Phase 1: Cleaning up old artifacts..."
rm -f reports/audit.log
log "Cleanup complete."

# --- Phase 2: Build & Test ---
log "Phase 2: Building all polyglot services (Orchestrator, Python, Java, Rust)..."
# This single command builds all Dockerfiles defined in the compose file.
# The '--parallel' flag can speed up builds on multi-core systems.
docker-compose build --parallel
log "All services built successfully."
# A real production pipeline would have a 'test' phase here for each plugin.

# --- Phase 3: Execution ---
log "Phase 3: Executing remediation playbook 'playbooks/remediate_compromised_host.yml'..."
# We run the orchestrator, which reads the playbook and executes plugins.
# The '--rm' flag ensures the container is removed after execution.
docker-compose run --rm orchestrator

if [ $? -ne 0 ]; then
    error "Orchestrator finished with an error. Check the audit log for details."
fi
log "Orchestrator finished successfully."

# --- Phase 4: Reporting ---
log "Phase 4: Displaying final audit trail from reports/audit.log..."
echo "=========================== AUDIT LOG START ==========================="
if [ -f "reports/audit.log" ]; then
    # Use 'cat -n' to add line numbers for clarity.
    cat -n reports/audit.log
else
    warn "Audit log not found."
fi
echo "============================ AUDIT LOG END ============================"

log "PSOR CI/CD Pipeline :: SUCCESS"
exit 0
