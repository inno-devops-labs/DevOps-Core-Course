package com.devopsinfo.service;

import com.devopsinfo.api.dto.EndpointInfo;
import com.devopsinfo.api.dto.HealthResponse;
import com.devopsinfo.api.dto.InfoResponse;
import com.devopsinfo.api.dto.RequestInfo;
import com.devopsinfo.api.dto.RuntimeInfo;
import com.devopsinfo.api.dto.ServiceInfo;
import com.devopsinfo.api.dto.SystemInfo;
import jakarta.servlet.http.HttpServletRequest;
import java.net.InetAddress;
import java.net.UnknownHostException;
import java.time.Duration;
import java.time.Instant;
import java.time.ZoneId;
import java.time.ZoneOffset;
import java.time.format.DateTimeFormatter;
import java.time.temporal.ChronoUnit;
import java.util.List;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

@Service
public class InfoService {

    private static final Logger log = LoggerFactory.getLogger(InfoService.class);

    private static final Instant START_TIME = Instant.now();
    private static final DateTimeFormatter ISO_UTC_MILLIS =
        DateTimeFormatter.ofPattern("yyyy-MM-dd'T'HH:mm:ss.SSSX").withZone(ZoneOffset.UTC);

    private static final ServiceInfo SERVICE_INFO = new ServiceInfo(
        "devops-info-service",
        "1.0.0",
        "DevOps course info service",
        "Spring Boot"
    );

    private static final List<EndpointInfo> ENDPOINTS = List.of(
        new EndpointInfo("/", "GET", "Service information"),
        new EndpointInfo("/health", "GET", "Health check")
    );

    public InfoResponse buildInfoResponse(HttpServletRequest request) {
        return new InfoResponse(
            SERVICE_INFO,
            getSystemInfo(),
            getRuntimeInfo(),
            getRequestInfo(request),
            ENDPOINTS
        );
    }

    public HealthResponse buildHealthResponse() {
        return new HealthResponse(
            "healthy",
            isoUtcNow(),
            getUptimeSeconds()
        );
    }

    private SystemInfo getSystemInfo() {
        String hostname = resolveHostname();
        String platform = System.getProperty("os.name", "unknown");
        String platformVersion = System.getProperty("os.version", "unknown");
        String architecture = System.getProperty("os.arch", "unknown");
        int cpuCount = Runtime.getRuntime().availableProcessors();
        String javaVersion = System.getProperty("java.version", "unknown");

        // Keep the Python-shaped field name from the lab for schema parity.
        String pythonVersion = "java-" + javaVersion;

        return new SystemInfo(
            hostname,
            platform,
            platformVersion,
            architecture,
            cpuCount,
            pythonVersion
        );
    }

    private RuntimeInfo getRuntimeInfo() {
        long uptimeSeconds = getUptimeSeconds();
        String uptimeHuman = formatUptime(uptimeSeconds);
        String timezone = ZoneId.systemDefault().getId();

        return new RuntimeInfo(
            uptimeSeconds,
            uptimeHuman,
            isoUtcNow(),
            timezone
        );
    }

    private RequestInfo getRequestInfo(HttpServletRequest request) {
        String clientIp = resolveClientIp(request);
        String userAgent = headerOrDefault(request, "User-Agent", "unknown");
        String method = request.getMethod();
        String path = request.getRequestURI();

        return new RequestInfo(clientIp, userAgent, method, path);
    }

    private String resolveHostname() {
        try {
            return InetAddress.getLocalHost().getHostName();
        } catch (UnknownHostException ex) {
            log.warn("Unable to resolve hostname: {}", ex.getMessage());
            return "unknown";
        }
    }

    private long getUptimeSeconds() {
        long seconds = Duration.between(START_TIME, Instant.now()).getSeconds();
        return Math.max(seconds, 0);
    }

    private String isoUtcNow() {
        Instant now = Instant.now().truncatedTo(ChronoUnit.MILLIS);
        return ISO_UTC_MILLIS.format(now);
    }

    private String resolveClientIp(HttpServletRequest request) {
        String forwardedFor = request.getHeader("X-Forwarded-For");
        if (forwardedFor != null && !forwardedFor.isBlank()) {
            String[] parts = forwardedFor.split(",");
            if (parts.length > 0) {
                return parts[0].trim();
            }
        }

        String remoteAddr = request.getRemoteAddr();
        return (remoteAddr == null || remoteAddr.isBlank()) ? "unknown" : remoteAddr;
    }

    private String headerOrDefault(HttpServletRequest request, String name, String fallback) {
        String value = request.getHeader(name);
        return (value == null || value.isBlank()) ? fallback : value;
    }

    private String formatUptime(long seconds) {
        long days = seconds / 86_400;
        long remainder = seconds % 86_400;
        long hours = remainder / 3_600;
        remainder = remainder % 3_600;
        long minutes = remainder / 60;
        long secs = remainder % 60;

        StringBuilder sb = new StringBuilder();
        if (days > 0) {
            sb.append(days).append(days == 1 ? " day, " : " days, ");
        }
        if (hours > 0 || days > 0) {
            sb.append(hours).append(hours == 1 ? " hour, " : " hours, ");
        }
        sb.append(minutes).append(minutes == 1 ? " minute, " : " minutes, ");
        sb.append(secs).append(secs == 1 ? " second" : " seconds");
        return sb.toString();
    }
}

