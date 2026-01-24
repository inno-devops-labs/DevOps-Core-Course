import com.sun.net.httpserver.HttpServer;
import com.sun.net.httpserver.HttpExchange;
import java.io.IOException;
import java.io.OutputStream;
import java.net.InetSocketAddress;
import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.time.Duration;
import java.time.ZoneOffset;
import java.time.format.DateTimeFormatter;
import java.lang.management.ManagementFactory;

public class Main {
    private static final Instant START_TIME = Instant.now();
    private static final String VERSION = "1.0.0";
    
    public static void main(String[] args) throws IOException {
        String host = System.getenv().getOrDefault("HOST", "0.0.0.0");
        int port = Integer.parseInt(System.getenv().getOrDefault("PORT", "8080"));
        
        HttpServer server = HttpServer.create(new InetSocketAddress(host, port), 0);
        
        server.createContext("/", Main::handleRoot);
        server.createContext("/health", Main::handleHealth);
        
        server.setExecutor(null);
        server.start();
        
        System.out.println("==================================================");
        System.out.println("DevOps Info Service starting...");
        System.out.println("Host: " + host);
        System.out.println("Port: " + port);
        System.out.println("Java: " + System.getProperty("java.version"));
        System.out.println("Endpoints: http://" + host + ":" + port + "/");
        System.out.println("==================================================");
    }
    
    private static void handleRoot(HttpExchange exchange) throws IOException {
        if (!"GET".equals(exchange.getRequestMethod())) {
            sendResponse(exchange, 405, "{\"error\":\"Method Not Allowed\"}");
            return;
        }
        
        String clientIp = exchange.getRemoteAddress().getAddress().getHostAddress();
        String userAgent = exchange.getRequestHeaders().getFirst("User-Agent");
        String method = exchange.getRequestMethod();
        String path = exchange.getRequestURI().getPath();
        
        String json = buildMainResponse(clientIp, userAgent, method, path);
        sendResponse(exchange, 200, json);
        
        System.out.println(String.format("%s Request: %s %s from %s",
            Instant.now().toString(), method, path, clientIp));
    }
    
    private static void handleHealth(HttpExchange exchange) throws IOException {
        if (!"GET".equals(exchange.getRequestMethod())) {
            sendResponse(exchange, 405, "{\"error\":\"Method Not Allowed\"}");
            return;
        }
        
        long uptimeSeconds = Duration.between(START_TIME, Instant.now()).getSeconds();
        String timestamp = Instant.now().atOffset(ZoneOffset.UTC)
            .format(DateTimeFormatter.ISO_INSTANT);
        
        String json = String.format(
            "{\"status\":\"healthy\",\"timestamp\":\"%s\",\"uptime_seconds\":%d}",
            timestamp, uptimeSeconds
        );
        
        sendResponse(exchange, 200, json);
    }
    
    private static String buildMainResponse(String clientIp, String userAgent, 
                                           String method, String path) {
        long uptimeSeconds = Duration.between(START_TIME, Instant.now()).getSeconds();
        long hours = uptimeSeconds / 3600;
        long minutes = (uptimeSeconds % 3600) / 60;
        String uptimeHuman = String.format("%d hour%s, %d minute%s", 
            hours, hours != 1 ? "s" : "",
            minutes, minutes != 1 ? "s" : "");
        
        String timestamp = Instant.now().atOffset(ZoneOffset.UTC)
            .format(DateTimeFormatter.ISO_INSTANT);
        
        Runtime runtime = Runtime.getRuntime();
        int cpuCount = runtime.availableProcessors();
        
        return String.format("""
            {
              "service": {
                "name": "devops-info-service",
                "version": "%s",
                "description": "DevOps course info service",
                "framework": "Java HttpServer"
              },
              "system": {
                "hostname": "%s",
                "platform": "%s",
                "platform_version": "%s",
                "architecture": "%s",
                "cpu_count": %d,
                "java_version": "%s"
              },
              "runtime": {
                "uptime_seconds": %d,
                "uptime_human": "%s",
                "current_time": "%s",
                "timezone": "UTC"
              },
              "request": {
                "client_ip": "%s",
                "user_agent": "%s",
                "method": "%s",
                "path": "%s"
              },
              "endpoints": [
                {"path": "/", "method": "GET", "description": "Service information"},
                {"path": "/health", "method": "GET", "description": "Health check"}
              ]
            }
            """,
            VERSION,
            getHostname(),
            System.getProperty("os.name"),
            System.getProperty("os.version"),
            System.getProperty("os.arch"),
            cpuCount,
            System.getProperty("java.version"),
            uptimeSeconds,
            uptimeHuman,
            timestamp,
            clientIp,
            userAgent != null ? userAgent : "unknown",
            method,
            path
        );
    }
    
    private static String getHostname() {
        try {
            return java.net.InetAddress.getLocalHost().getHostName();
        } catch (Exception e) {
            return "unknown";
        }
    }
    
    private static void sendResponse(HttpExchange exchange, int statusCode, String response) 
            throws IOException {
        exchange.getResponseHeaders().set("Content-Type", "application/json");
        byte[] bytes = response.getBytes(StandardCharsets.UTF_8);
        exchange.sendResponseHeaders(statusCode, bytes.length);
        try (OutputStream os = exchange.getResponseBody()) {
            os.write(bytes);
        }
    }
}