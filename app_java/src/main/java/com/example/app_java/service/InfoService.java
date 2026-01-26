package com.example.app_java.service;

import java.lang.management.ManagementFactory;
import java.lang.management.OperatingSystemMXBean;
import java.net.InetAddress;
import java.net.UnknownHostException;
import java.time.Duration;
import java.time.ZoneOffset;
import java.time.ZonedDateTime;
import java.time.format.DateTimeFormatter;
import java.util.List;
import java.util.Optional;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.web.context.request.RequestContextHolder;
import org.springframework.web.context.request.ServletRequestAttributes;

import com.example.app_java.dto.EndpointInfo;
import com.example.app_java.dto.HealthResponse;
import com.example.app_java.dto.InfoResponse;
import com.example.app_java.dto.RequestInfo;
import com.example.app_java.dto.RuntimeInfo;
import com.example.app_java.dto.ServiceInfo;
import com.example.app_java.dto.SystemInfo;

import jakarta.servlet.http.HttpServletRequest;

@Service
public class InfoService {
    private static final Logger log = LoggerFactory.getLogger(InfoService.class);
    private static ZonedDateTime START_TIME = ZonedDateTime.now(ZoneOffset.UTC);

    private static final List<EndpointInfo> endpoints = List.of(
            new EndpointInfo("/", "GET", "Service information"),
            new EndpointInfo("/health", "GET", "Health check"));

    @Value("${spring.application.name}")
    private String appName;

    @Value("${spring.application.version}")
    private String appVersion;

    @Value("${spring.application.description}")
    private String appDescription;

    public InfoResponse getAppInfo() {
        return new InfoResponse(getServiceInfo(), getSystemInfo(), getRuntimeInfo(), getRequestInfo(), endpoints);
    }

    public HealthResponse getHealthStatus() {
        HealthResponse response = new HealthResponse();

        ZonedDateTime now = ZonedDateTime.now(ZoneOffset.UTC);
        Duration uptime = Duration.between(START_TIME, now);
        response.setStatus("healthy");
        response.setTimestamp(ZonedDateTime.now(ZoneOffset.UTC).format(DateTimeFormatter.ISO_INSTANT));
        response.setUptimeSeconds(uptime.toSeconds());

        return response;
    }

    private SystemInfo getSystemInfo() {
        SystemInfo info = new SystemInfo();

        try {
            info.setHostname(InetAddress.getLocalHost().getHostName());
        } catch (UnknownHostException e) {
            info.setHostname("unknown");
            log.warn("Could not determine hostname", e);
        }

        info.setPlatform(System.getProperty("os.name"));
        info.setPlatformVersion(System.getProperty("os.version"));
        info.setArchitecture(System.getProperty("os.arch"));
        info.setJavaVersion(System.getProperty("java.version"));

        OperatingSystemMXBean osBean = ManagementFactory.getOperatingSystemMXBean();
        info.setCpuCount(osBean.getAvailableProcessors());

        return info;
    }

    private ServiceInfo getServiceInfo() {
        ServiceInfo serviceInfo = new ServiceInfo();
        serviceInfo.setName(appName);
        serviceInfo.setVersion(appVersion);
        serviceInfo.setDescription(appDescription);
        serviceInfo.setFramework("Spring Boot");

        return serviceInfo;
    }

    private RuntimeInfo getRuntimeInfo() {
        RuntimeInfo info = new RuntimeInfo();

        ZonedDateTime now = ZonedDateTime.now(ZoneOffset.UTC);

        Duration uptime = Duration.between(START_TIME, now);
        info.setUptimeSeconds(uptime.toSeconds());
        info.setUptimeHuman(formatUptime(uptime));
        info.setCurrentTime(now.format(DateTimeFormatter.ISO_INSTANT));
        info.setTimezone("UTC");

        return info;
    }

    private String formatUptime(Duration duration) {
        long seconds = duration.toSeconds();
        long hours = seconds / 3600;
        long minutes = (seconds % 3600) / 60;

        return String.format("%d hours, %d minutes", hours, minutes);
    }

    private RequestInfo getRequestInfo() {
        RequestInfo info = new RequestInfo();

        Optional<HttpServletRequest> request = getCurrentHttpRequest();

        if (request.isPresent()) {
            HttpServletRequest httpRequest = request.get();
            info.setClientIp(getClientIp(httpRequest));
            info.setUserAgent(httpRequest.getHeader("User-Agent"));
            info.setMethod(httpRequest.getMethod());
            info.setPath(httpRequest.getRequestURI());
        } else {
            info.setClientIp("unknown");
            info.setUserAgent("unknown");
            info.setMethod("unknown");
            info.setPath("unknown");
        }

        return info;
    }

    private String getClientIp(HttpServletRequest request) {
        String xForwardedFor = request.getHeader("X-Forwarded-For");
        if (xForwardedFor != null && !xForwardedFor.isEmpty()) {
            return xForwardedFor.split(",")[0].trim();
        }
        return request.getRemoteAddr();
    }

    private Optional<HttpServletRequest> getCurrentHttpRequest() {
        return Optional.ofNullable(RequestContextHolder.getRequestAttributes())
                .filter(ServletRequestAttributes.class::isInstance)
                .map(ServletRequestAttributes.class::cast)
                .map(ServletRequestAttributes::getRequest);
    }
}
