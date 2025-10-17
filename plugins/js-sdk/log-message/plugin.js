const sdk = require('psor-sdk-lib'); // Import the SDK

function main() {
    const params = sdk.parseArgs();
    const messageToLog = params.message;

    if (!messageToLog) {
        sdk.errorResponse("Missing parameter: message");
    }

    // Simulate logging the message
    const reportMessage = `Successfully logged message: '${messageToLog}'`;
    console.warn(`*** PLUGIN SIMULATION: ${reportMessage} ***`); // Simulate action

    sdk.successResponse(reportMessage, params);
}

main();
