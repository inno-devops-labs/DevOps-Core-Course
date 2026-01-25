package devops.core.app_java.dto;

public record RequestBlock(
        String clientIp,
        String userAgent,
        String method,
        String path
) {}