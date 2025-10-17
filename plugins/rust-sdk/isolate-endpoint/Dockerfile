# --- Build Stage ---
FROM rust:1-slim AS build

# Set base WORKDIR
WORKDIR /usr/src/app

RUN rustup target add x86_64-unknown-linux-musl

# Copy both crates relative to the base WORKDIR
COPY ./psor-sdk-lib ./psor-sdk-lib
COPY ./isolate-endpoint ./isolate-endpoint

# Change the working directory *into* the plugin's directory
WORKDIR /usr/src/app/isolate-endpoint

# Build the plugin (Cargo runs from within 'isolate-endpoint')
RUN cargo build --release --target x86_64-unknown-linux-musl

# --- Run Stage ---
FROM scratch
WORKDIR /

# --- THIS IS THE ADJUSTED PATH ---
# Try copying from the target directory relative to the plugin's WORKDIR
COPY --from=build /usr/src/app/isolate-endpoint/target/x86_64-unknown-linux-musl/release/isolate-endpoint .
# --- END ADJUSTMENT ---

ENTRYPOINT ["/isolate-endpoint"]
