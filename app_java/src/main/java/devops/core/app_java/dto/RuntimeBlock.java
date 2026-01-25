package devops.core.app_java.dto;

public record RuntimeBlock(
        long uptimeSeconds,
        String uptimeHuman,
        String currentTime,
        String timezone
) {}