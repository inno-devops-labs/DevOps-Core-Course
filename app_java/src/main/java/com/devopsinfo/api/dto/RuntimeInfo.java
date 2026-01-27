package com.devopsinfo.api.dto;

import com.fasterxml.jackson.annotation.JsonProperty;

public record RuntimeInfo(
    @JsonProperty("uptime_seconds")
    long uptimeSeconds,
    @JsonProperty("uptime_human")
    String uptimeHuman,
    @JsonProperty("current_time")
    String currentTime,
    String timezone
) {
}

