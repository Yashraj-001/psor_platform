# --- Build Stage ---
FROM rust:1-slim AS build

# Context is rust-sdk/
WORKDIR /usr/src/app

RUN rustup target add x86_64-unknown-linux-musl

# Copy both crates relative to the base WORKDIR
COPY ./psor-sdk-lib ./psor-sdk-lib
COPY ./unisolate-endpoint ./unisolate-endpoint

# Change the working directory *into* this plugin's directory
WORKDIR /usr/src/app/unisolate-endpoint

# Build this specific plugin
RUN cargo build --release --target x86_64-unknown-linux-musl

# --- Run Stage ---
FROM scratch
WORKDIR /
# --- THIS IS THE FIX ---
# Copy from this plugin's (unisolate-endpoint) target directory
COPY --from=build /usr/src/app/unisolate-endpoint/target/x86_64-unknown-linux-musl/release/unisolate-endpoint .
# --- END FIX ---
ENTRYPOINT ["/unisolate-endpoint"]
