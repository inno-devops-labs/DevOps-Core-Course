package devops.core.app_java.configuration;

import org.springframework.boot.context.properties.ConfigurationProperties;

@ConfigurationProperties(prefix = "app.service")
public record ServiceInfoProperties(
        String name,
        String version,
        String description
) {}
