FROM python:3.10-slim AS builder
# Stage 1: Copy the entire build context (python-sdk)
WORKDIR /build-context
COPY . .

FROM python:3.10-slim
# Stage 2: Final image
WORKDIR /app
RUN pip install jira

# Copy files FROM the builder stage's context directory
COPY --from=builder /build-context/psor_sdk.py /app/psor_sdk.py
COPY --from=builder /build-context/revoke-iam-key/plugin.py /app/plugin.py

ENTRYPOINT ["python3", "/app/plugin.py"]
