package devops.core.app_java.dto;

public record HealthResponse(
        String status,
        String timestamp,
        long uptimeSeconds
) {}
