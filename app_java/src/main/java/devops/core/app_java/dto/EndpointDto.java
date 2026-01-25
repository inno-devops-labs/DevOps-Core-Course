package devops.core.app_java.dto;

public record EndpointDto(
        String path,
        String method,
        String description
) {}
