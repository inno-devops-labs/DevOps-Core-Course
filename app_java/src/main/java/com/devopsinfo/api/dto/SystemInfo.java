package com.devopsinfo.api.dto;

import com.fasterxml.jackson.annotation.JsonProperty;

public record SystemInfo(
    String hostname,
    String platform,
    @JsonProperty("platform_version")
    String platformVersion,
    String architecture,
    @JsonProperty("cpu_count")
    int cpuCount,
    @JsonProperty("python_version")
    String pythonVersion
) {
}

