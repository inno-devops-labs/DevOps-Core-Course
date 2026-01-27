package com.devopsinfo.api.dto;

public record ServiceInfo(
    String name,
    String version,
    String description,
    String framework
) {
}

