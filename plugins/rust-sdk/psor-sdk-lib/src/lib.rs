use std::collections::HashMap;
use std::env;
use serde::Serialize;

#[derive(Serialize)]
struct JsonResult<T: Serialize> {
    status: String,
    message: String,
    details: Option<T>,
}

/// Parses command-line arguments (key=value) into a HashMap.
pub fn parse_args() -> HashMap<String, String> {
    env::args().skip(1) // Skip the program name
        .filter_map(|arg| {
            if let Some((key, value)) = arg.split_once('=') {
                Some((key.to_string(), value.to_string()))
            } else {
                eprintln!("Warning: Malformed argument ignored: {}", arg);
                None
            }
        })
        .collect()
}

/// Prints a standardized JSON success response and exits 0.
pub fn success_response<T: Serialize>(message: &str, details: Option<T>) {
    let response = JsonResult {
        status: "success".to_string(),
        message: message.to_string(),
        details,
    };
    println!("{}", serde_json::to_string(&response).unwrap_or_default());
    std::process::exit(0);
}

/// Prints a standardized JSON error response, optionally prints to stderr, and exits non-zero.
pub fn error_response(message: &str, exit_code: i32, stderr_message: Option<&str>) {
    let response = JsonResult::<()> { // No details needed for error
        status: "error".to_string(),
        message: message.to_string(),
        details: None,
    };
    println!("{}", serde_json::to_string(&response).unwrap_or_default());
    if let Some(stderr_msg) = stderr_message {
        eprintln!("{}", stderr_msg);
    }
    std::process::exit(exit_code);
}
