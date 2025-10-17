package com.psor.sdk;

import java.util.Arrays;
import java.util.Map;
import java.util.stream.Collectors;

public class PluginSDK {

    /**
     * Parses command-line arguments (key=value) into a Map.
     */
    public static Map<String, String> parseArgs(String[] args) {
        return Arrays.stream(args)
            .filter(s -> s.contains("="))
            .map(s -> s.split("=", 2))
            .collect(Collectors.toMap(a -> a[0], a -> a.length > 1 ? a[1] : "", (v1, v2) -> v1)); // Handle duplicate keys if necessary
    }

    /**
     * Prints a standardized JSON success response to stdout and exits with 0.
     */
    public static void successResponse(String message, Map<String, String> details) {
        // Simple manual JSON creation for minimal dependencies
        StringBuilder json = new StringBuilder();
        json.append("{\"status\":\"success\", \"message\":\"").append(escapeJson(message)).append("\"");
        if (details != null && !details.isEmpty()) {
            json.append(", \"details\":{");
            json.append(details.entrySet().stream()
                .map(entry -> "\"" + escapeJson(entry.getKey()) + "\":\"" + escapeJson(entry.getValue()) + "\"")
                .collect(Collectors.joining(",")));
            json.append("}");
        }
        json.append("}");
        System.out.println(json.toString());
        System.exit(0);
    }

    /**
     * Prints a standardized JSON error response to stdout, optionally prints to stderr, and exits non-zero.
     */
    public static void errorResponse(String message, int exitCode, String stderrMessage) {
        StringBuilder json = new StringBuilder();
        json.append("{\"status\":\"error\", \"message\":\"").append(escapeJson(message)).append("\"}");
        System.out.println(json.toString());
        if (stderrMessage != null && !stderrMessage.isEmpty()) {
            System.err.println(stderrMessage);
        }
        System.exit(exitCode);
    }

    // Basic JSON string escaping
    private static String escapeJson(String s) {
        return s.replace("\\", "\\\\")
                .replace("\"", "\\\"")
                .replace("\b", "\\b")
                .replace("\f", "\\f")
                .replace("\n", "\\n")
                .replace("\r", "\\r")
                .replace("\t", "\\t");
    }
}
