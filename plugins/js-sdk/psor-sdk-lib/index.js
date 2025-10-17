/**
 * Parses command-line arguments (key=value) into an object.
 */
function parseArgs() {
    const params = {};
    // Start from index 2 to skip node executable and script name
    process.argv.slice(2).forEach(arg => {
        try {
            const [key, value] = arg.split('=', 2);
            if (key !== undefined && value !== undefined) {
                params[key] = value;
            } else {
                console.warn(`Warning: Malformed argument ignored: ${arg}`);
            }
        } catch (e) {
             console.warn(`Warning: Error parsing argument "${arg}": ${e.message}`);
        }
    });
    return params;
}

/**
 * Prints standardized JSON success response and exits 0.
 */
function successResponse(message, details = null) {
    const response = { status: "success", message };
    if (details) {
        response.details = details;
    }
    console.log(JSON.stringify(response));
    process.exit(0);
}

/**
 * Prints standardized JSON error response, optionally prints to stderr, and exits non-zero.
 */
function errorResponse(message, exitCode = 1, stderrMessage = null) {
    const response = { status: "error", message };
    console.log(JSON.stringify(response));
    if (stderrMessage) {
        console.error(stderrMessage);
    }
    process.exit(exitCode);
}

module.exports = { parseArgs, successResponse, errorResponse };
