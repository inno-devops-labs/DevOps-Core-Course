package devops.core.app_java.dto;

import java.util.List;

public record InfoResponse(
        ServiceBlock service,
        SystemBlock system,
        RuntimeBlock runtime,
        RequestBlock request,
        List<EndpointDto> endpoints
) {}
