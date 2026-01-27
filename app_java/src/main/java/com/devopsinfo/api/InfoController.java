package com.devopsinfo.api;

import com.devopsinfo.api.dto.HealthResponse;
import com.devopsinfo.api.dto.InfoResponse;
import com.devopsinfo.service.InfoService;
import jakarta.servlet.http.HttpServletRequest;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class InfoController {

    private final InfoService infoService;

    public InfoController(InfoService infoService) {
        this.infoService = infoService;
    }

    @GetMapping("/")
    public InfoResponse index(HttpServletRequest request) {
        return infoService.buildInfoResponse(request);
    }

    @GetMapping("/health")
    public HealthResponse health() {
        return infoService.buildHealthResponse();
    }
}

