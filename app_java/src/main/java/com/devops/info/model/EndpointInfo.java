package com.devops.info.model;

public class EndpointInfo {
    private String path;
    private String method;
    private String description;

    // Getters and Setters
    public String getPath() { return path; }
    public void setPath(String path) { this.path = path; }

    public String getMethod() { return method; }
    public void setMethod(String method) { this.method = method; }

    public String getDescription() { return description; }
    public void setDescription(String description) { this.description = description; }
}
