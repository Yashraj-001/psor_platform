FROM python:3.10-slim
WORKDIR /app

# We need the Docker client to run sibling containers
RUN pip install docker pyyaml

COPY orchestrator.py .
CMD ["python3", "orchestrator.py", "playbooks/remediate_compromised_host.yml"]
