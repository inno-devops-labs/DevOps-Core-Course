package devops.core.app_java.service;


import devops.core.app_java.configuration.ServiceInfoProperties;
import devops.core.app_java.dto.*;
import jakarta.servlet.http.HttpServletRequest;
import org.springframework.stereotype.Service;
import java.lang.management.ManagementFactory;
import java.net.InetAddress;
import java.time.Instant;
import java.time.ZoneOffset;
import java.util.List;
import java.util.Optional;

/**
 * Creates result DTOs.
 */
@Service
public class InfoService {

    private final ServiceInfoProperties props;

    public InfoService(ServiceInfoProperties props) {
        this.props = props;
    }

    public InfoResponse buildInfoResponse(HttpServletRequest request) {
        var uptime = uptime();
        return new InfoResponse(
                new ServiceBlock(props.name(), props.version(), props.description(), "Spring Boot"),
                systemInfo(),
                new RuntimeBlock(uptime.seconds(), uptime.human(), isoUtcNow(), "UTC"),
                requestInfo(request),
                endpoints()
        );
    }

    public HealthResponse buildHealthResponse() {
        var uptime = uptime();
        return new HealthResponse("healthy", isoUtcNow(), uptime.seconds());
    }

    private SystemBlock systemInfo() {
        try {
            String hostname = InetAddress.getLocalHost().getHostName();
            String osName = System.getProperty("os.name");
            String osVersion = System.getProperty("os.version");
            String arch = System.getProperty("os.arch");
            int cpuCount = Runtime.getRuntime().availableProcessors();
            String javaVersion = System.getProperty("java.version");

            return new SystemBlock(hostname, osName, osVersion, arch, cpuCount, javaVersion);
        } catch (Exception e) {
            // fallback without hostname if resolution fails
            String osName = System.getProperty("os.name");
            String osVersion = System.getProperty("os.version");
            String arch = System.getProperty("os.arch");
            int cpuCount = Runtime.getRuntime().availableProcessors();
            String javaVersion = System.getProperty("java.version");

            return new SystemBlock("unknown", osName, osVersion, arch, cpuCount, javaVersion);
        }
    }

    private RequestBlock requestInfo(HttpServletRequest request) {
        String xff = Optional.ofNullable(request.getHeader("X-Forwarded-For"))
                .map(h -> h.split(",")[0].trim())
                .orElse("");

        String clientIp = !xff.isBlank() ? xff : request.getRemoteAddr();
        String userAgent = Optional.ofNullable(request.getHeader("User-Agent")).orElse("");

        return new RequestBlock(clientIp, userAgent, request.getMethod(), request.getRequestURI());
    }

    private List<EndpointDto> endpoints() {
        return List.of(
                new EndpointDto("/", "GET", "Service information"),
                new EndpointDto("/health", "GET", "Health check")
        );
    }

    private String isoUtcNow() {
        return Instant.now().atOffset(ZoneOffset.UTC).toString();
    }

    private Uptime uptime() {
        long uptimeSeconds = ManagementFactory.getRuntimeMXBean().getUptime() / 1000;

        long hours = uptimeSeconds / 3600;
        long minutes = (uptimeSeconds % 3600) / 60;
        String human = hours + " hour" + (hours == 1 ? "" : "s") + ", " + minutes + " minute" + (minutes == 1 ? "" : "s");

        return new Uptime(uptimeSeconds, human);
    }

    private record Uptime(long seconds, String human) {}
}