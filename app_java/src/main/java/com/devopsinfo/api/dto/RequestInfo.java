package com.devopsinfo.api.dto;

import com.fasterxml.jackson.annotation.JsonProperty;

public record RequestInfo(
    @JsonProperty("client_ip")
    String clientIp,
    @JsonProperty("user_agent")
    String userAgent,
    String method,
    String path
) {
}

