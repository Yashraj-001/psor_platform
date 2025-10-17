package com.remediation;

import com.psor.sdk.PluginSDK;
import java.util.Map;

public class UnblockIpPlugin {
    public static void main(String[] args) {
        Map<String, String> params = PluginSDK.parseArgs(args);
        String ipAddress = params.get("ip_address");

        if (ipAddress == null || ipAddress.isEmpty()) {
            PluginSDK.errorResponse("Missing parameter: ip_address", 1, null);
        }

        // *** REAL WORK: Use firewall/WAF API client to REMOVE block rule for ipAddress ***
        System.err.println(String.format("*** SIMULATION: Would remove block rule for IP '%s' ***", ipAddress)); 
        
        String message = String.format("Successfully submitted request to UNBLOCK IP address '%s'.", ipAddress);
        PluginSDK.successResponse(message, params); 
    }
}
