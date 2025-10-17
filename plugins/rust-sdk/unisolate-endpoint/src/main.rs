use psor_sdk::{parse_args, success_response, error_response}; // Use the correct library name 'psor_sdk'
use serde::Serialize;

#[derive(Serialize)]
struct UnisolateDetails {
    endpoint_id: String,
}

fn main() {
    let params = parse_args(); 

    if let Some(endpoint_id) = params.get("endpoint_id") {
        
        eprintln!("*** SIMULATION: Would remove network isolation for endpoint '{}' ***", endpoint_id); 

        let message = format!("Successfully submitted request to UNISOLATE endpoint '{}'.", endpoint_id);
        let details = UnisolateDetails { endpoint_id: endpoint_id.clone() };
        success_response(&message, Some(details)); 
    } else {
        error_response("Missing parameter: endpoint_id", 1, None); 
    }
}
