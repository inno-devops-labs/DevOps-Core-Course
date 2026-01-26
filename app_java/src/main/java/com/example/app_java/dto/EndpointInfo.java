package com.example.app_java.dto;

public class EndpointInfo {
    private String path;
    private String method;
    private String description;
    
    public EndpointInfo(String path, String method, String description) {
        this.path = path;
        this.method = method;
        this.description = description;
    }
    public String getPath() {
        return path;
    }
    public String getMethod() {
        return method;
    }
    public String getDescription() {
        return description;
    }
    public void setPath(String path) {
        this.path = path;
    }
    public void setMethod(String method) {
        this.method = method;
    }
    public void setDescription(String description) {
        this.description = description;
    }
}
