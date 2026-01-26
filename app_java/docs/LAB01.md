
## Best Practices Applied
### Clean Code Organization
```java
# Grouped and ordered imports
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

import com.example.app_java.dto.HealthResponse;
import com.example.app_java.dto.InfoResponse;
import com.example.app_java.service.InfoService;

import jakarta.servlet.ServletRequest;
```
Importance: Proper import organization improves readability and avoids circular dependencies.

### Separation of Concerns
```java
private ServiceInfo getServiceInfo() {
        ServiceInfo serviceInfo = new ServiceInfo();
        serviceInfo.setName(appName);
        ...
    }

    private RuntimeInfo getRuntimeInfo() {
        RuntimeInfo info = new RuntimeInfo();

        ZonedDateTime now = ZonedDateTime.now(ZoneOffset.UTC);
        ...
    }
```

Importance: Each function has a single responsibility, making code easier to test, maintain, and reuse.



### Environment-Based Configuration

```
server.address=${HOST:localhost}
server.port=${PORT:5000}
debug=${DEBUG:false}
```

Importance: Allows configuration changes without code modifications

### Logging
```java
private static final Logger log = LoggerFactory.getLogger(InfoController.class);

log.info("GET / requested from {}", request.getRemoteAddr());
```

Importance: Provides operational monitoring


### Error Handling
```java
@RestControllerAdvice
public class GlobalExceptionHandler {
    
    private static final Logger log = LoggerFactory.getLogger(GlobalExceptionHandler.class);
    
    @ExceptionHandler(NoHandlerFoundException.class)
    public ResponseEntity<ErrorResponse> handleNotFound(NoHandlerFoundException ex, 
                                                      HttpServletRequest request) {
        ErrorResponse error = new ErrorResponse();
        error.setError("Not Found");
        error.setMessage(String.format("Endpoint %s does not exist", request.getRequestURI()));
        error.setTimestamp(ZonedDateTime.now(ZoneOffset.UTC).format(DateTimeFormatter.ISO_INSTANT));
        
        log.warn("404 Not Found: {}", request.getRequestURI());
        
        return ResponseEntity.status(HttpStatus.NOT_FOUND).body(error);
    }
    
    @ExceptionHandler(Exception.class)
    public ResponseEntity<ErrorResponse> handleGenericException(Exception ex, 
                                                              HttpServletRequest request) {
        ...
    }
}
```
Importance: Provides clear error messages to users, prevents leakage of internal information


## API Documentation

### GET /

Request: curl -X GET "http://localhost:5000/" 

Response:
```json
{"service":{"name":"devops-info-service","version":"1.0.0","description":"DevOps course info service","framework":"Spring Boot"},"system":{"hostname":"DESKTOP-2Q0E6TS","platform":"Windows 10","platformVersion":"10.0","architecture":"amd64","cpuCount":8,"javaVersion":"25"},"runtime":{"uptimeSeconds":148,"uptimeHuman":"0 hours, 2 minutes","currentTime":"2026-01-26T07:36:11.610985500Z","timezone":"UTC"},"request":{"clientIp":"127.0.0.1","userAgent":"curl/8.13.0","method":"GET","path":"/"},"endpoints":[{"path":"/","method":"GET","description":"Service information"},{"path":"/health","method":"GET","description":"Health check"}]}
```
### GET /health

Request: curl -X GET "http://localhost:5000/health"

Response:
```json
{"status":"healthy","timestamp":"2026-01-26T07:38:08.945379700Z","uptimeSeconds":265}
```

## Testing Evidence

Terminal Output
```
2026-01-26T10:33:43.588+03:00  INFO 3276 --- [devops-info-service] [           main] o.s.b.w.embedded.tomcat.TomcatWebServer  : Tomcat started on 
port 5000 (http) with context path '/'
2026-01-26T10:33:43.625+03:00  INFO 3276 --- [devops-info-service] [           main] c.example.app_java.AppJavaApplication    : Started AppJavaApplication in 2.77 seconds (process running for 3.364)
2026-01-26T10:36:11.543+03:00  INFO 3276 --- [devops-info-service] [0.1-5000-exec-1] o.a.c.c.C.[Tomcat].[localhost].[/]       : Initializing Spring DispatcherServlet 'dispatcherServlet'
2026-01-26T10:36:11.544+03:00  INFO 3276 --- [devops-info-service] [0.1-5000-exec-1] o.s.web.servlet.DispatcherServlet        : Initializing Servlet 'dispatcherServlet'
2026-01-26T10:36:11.546+03:00  INFO 3276 --- [devops-info-service] [0.1-5000-exec-1] o.s.web.servlet.DispatcherServlet        : Completed initialization in 1 ms
2026-01-26T10:36:11.600+03:00  INFO 3276 --- [devops-info-service] [0.1-5000-exec-1] c.e.app_java.controller.InfoController   : GET / requested from 127.0.0.1
```

## Size comparision

The size of .jar file is 20mb

The size of app.py with venv is 40mb
