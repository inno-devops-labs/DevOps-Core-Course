package com.example.app_java.dto;

import java.util.List;

public class InfoResponse {
    private ServiceInfo service;
    private SystemInfo system;
    private RuntimeInfo runtime;
    private RequestInfo request;
    private List<EndpointInfo> endpoints;
    
    public InfoResponse(ServiceInfo service, SystemInfo system, RuntimeInfo runtime, RequestInfo request,
            List<EndpointInfo> endpoints) {
        this.service = service;
        this.system = system;
        this.runtime = runtime;
        this.request = request;
        this.endpoints = endpoints;
    }
    public ServiceInfo getService() {
        return service;
    }
    public SystemInfo getSystem() {
        return system;
    }
    public RuntimeInfo getRuntime() {
        return runtime;
    }
    public RequestInfo getRequest() {
        return request;
    }
    public List<EndpointInfo> getEndpoints() {
        return endpoints;
    }
    public void setService(ServiceInfo service) {
        this.service = service;
    }
    public void setSystem(SystemInfo system) {
        this.system = system;
    }
    public void setRuntime(RuntimeInfo runtime) {
        this.runtime = runtime;
    }
    public void setRequest(RequestInfo request) {
        this.request = request;
    }
    public void setEndpoints(List<EndpointInfo> endpoints) {
        this.endpoints = endpoints;
    }
}
