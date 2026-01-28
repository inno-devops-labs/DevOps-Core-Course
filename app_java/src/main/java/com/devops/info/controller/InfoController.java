package com.devops.info.controller;

import com.devops.info.model.*;
import jakarta.servlet.http.HttpServletRequest;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

import java.lang.management.ManagementFactory;
import java.net.InetAddress;
import java.time.Instant;
import java.time.ZoneId;
import java.time.format.DateTimeFormatter;
import java.util.List;

/**
 * REST controller providing service and system information
 */
@RestController
public class InfoController {

    @Value("${app.version:1.0.0}")
    private String appVersion;

    private final long startTime = System.currentTimeMillis();

    @GetMapping("/")
    public ServiceResponse getInfo(HttpServletRequest request) {
        ServiceResponse response = new ServiceResponse();
        
        // Service information
        ServiceInfo serviceInfo = new ServiceInfo();
        serviceInfo.setName("devops-info-service");
        serviceInfo.setVersion(appVersion);
        serviceInfo.setDescription("DevOps course info service");
        serviceInfo.setFramework("Spring Boot");
        response.setService(serviceInfo);

        // System information
        SystemInfo systemInfo = new SystemInfo();
        try {
            systemInfo.setHostname(InetAddress.getLocalHost().getHostName());
        } catch (Exception e) {
            systemInfo.setHostname("unknown");
        }
        systemInfo.setPlatform(System.getProperty("os.name"));
        systemInfo.setPlatformVersion(System.getProperty("os.version"));
        systemInfo.setArchitecture(System.getProperty("os.arch"));
        systemInfo.setCpuCount(Runtime.getRuntime().availableProcessors());
        systemInfo.setPythonVersion(System.getProperty("java.version"));
        response.setSystem(systemInfo);

        // Runtime information
        RuntimeInfo runtimeInfo = new RuntimeInfo();
        long uptimeSeconds = (System.currentTimeMillis() - startTime) / 1000;
        runtimeInfo.setUptimeSeconds(uptimeSeconds);
        runtimeInfo.setUptimeHuman(formatUptime(uptimeSeconds));
        runtimeInfo.setCurrentTime(Instant.now().toString());
        runtimeInfo.setTimezone("UTC");
        response.setRuntime(runtimeInfo);

        // Request information
        RequestInfo requestInfo = new RequestInfo();
        requestInfo.setClientIp(request.getRemoteAddr());
        requestInfo.setUserAgent(request.getHeader("User-Agent") != null ? 
                                 request.getHeader("User-Agent") : "Unknown");
        requestInfo.setMethod(request.getMethod());
        requestInfo.setPath(request.getRequestURI());
        response.setRequest(requestInfo);

        // Endpoints list
        EndpointInfo mainEndpoint = new EndpointInfo();
        mainEndpoint.setPath("/");
        mainEndpoint.setMethod("GET");
        mainEndpoint.setDescription("Service information");

        EndpointInfo healthEndpoint = new EndpointInfo();
        healthEndpoint.setPath("/health");
        healthEndpoint.setMethod("GET");
        healthEndpoint.setDescription("Health check");

        response.setEndpoints(List.of(mainEndpoint, healthEndpoint));

        return response;
    }

    @GetMapping("/health")
    public HealthResponse getHealth() {
        HealthResponse health = new HealthResponse();
        health.setStatus("healthy");
        health.setTimestamp(Instant.now().toString());
        health.setUptimeSeconds((System.currentTimeMillis() - startTime) / 1000);
        return health;
    }

    private String formatUptime(long seconds) {
        long hours = seconds / 3600;
        long minutes = (seconds % 3600) / 60;
        return String.format("%d hours, %d minutes", hours, minutes);
    }
}
