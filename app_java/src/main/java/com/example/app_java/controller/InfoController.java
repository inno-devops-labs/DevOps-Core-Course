package com.example.app_java.controller;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

import com.example.app_java.dto.HealthResponse;
import com.example.app_java.dto.InfoResponse;
import com.example.app_java.service.InfoService;

import jakarta.servlet.ServletRequest;


@RestController
public class InfoController {
    private static final Logger log = LoggerFactory.getLogger(InfoController.class);

    private final InfoService infoService;

    public InfoController(InfoService infoService) {
        this.infoService = infoService;
    }

    @GetMapping("/")
    public ResponseEntity<InfoResponse> getServiceInfo(ServletRequest request) {
         log.info("GET / requested from {}", request.getRemoteAddr());
        return ResponseEntity.ok().body(infoService.getAppInfo());
    }
    
    @GetMapping("/health")
    public ResponseEntity<HealthResponse> healthCheck() {
        log.debug("Health check requested");
        return ResponseEntity.ok().body(infoService.getHealthStatus());
    }
    
}
