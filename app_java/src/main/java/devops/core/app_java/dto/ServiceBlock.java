package devops.core.app_java.dto;

public record ServiceBlock(
        String name,
        String version,
        String description,
        String framework
) {}