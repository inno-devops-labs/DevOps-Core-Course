package com.devopsinfo.api.dto;

import java.util.List;

public record InfoResponse(
    ServiceInfo service,
    SystemInfo system,
    RuntimeInfo runtime,
    RequestInfo request,
    List<EndpointInfo> endpoints
) {
}

