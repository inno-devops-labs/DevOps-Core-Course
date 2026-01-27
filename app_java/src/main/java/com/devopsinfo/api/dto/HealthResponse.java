package com.devopsinfo.api.dto;

import com.fasterxml.jackson.annotation.JsonProperty;

public record HealthResponse(
    String status,
    String timestamp,
    @JsonProperty("uptime_seconds")
    long uptimeSeconds
) {
}

