package com.devopsinfo.api.dto;

public record EndpointInfo(
    String path,
    String method,
    String description
) {
}

