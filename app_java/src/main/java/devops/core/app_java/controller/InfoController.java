package devops.core.app_java.controller;

import devops.core.app_java.dto.HealthResponse;
import devops.core.app_java.dto.InfoResponse;
import devops.core.app_java.service.InfoService;
import jakarta.servlet.http.HttpServletRequest;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class InfoController {

    private static final Logger log = LoggerFactory.getLogger(InfoController.class);

    private final InfoService infoService;

    public InfoController(InfoService infoService) {
        this.infoService = infoService;
    }

    @GetMapping("/")
    public InfoResponse index(HttpServletRequest request) {
        log.info("Request {} {} from {}", request.getMethod(), request.getRequestURI(), request.getRemoteAddr());
        return infoService.buildInfoResponse(request);
    }

    @GetMapping("/health")
    public HealthResponse health() {
        return infoService.buildHealthResponse();
    }
}
