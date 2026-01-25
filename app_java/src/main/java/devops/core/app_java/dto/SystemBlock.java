package devops.core.app_java.dto;

public record SystemBlock(
        String hostname,
        String platform,
        String platformVersion,
        String architecture,
        int cpuCount,
        String javaVersion
) {}