package com.devops.info.model;

public class ServiceInfo {
    private String name;
    private String version;
    private String description;
    private String framework;

    // Getters and Setters
    public String getName() { return name; }
    public void setName(String name) { this.name = name; }

    public String getVersion() { return version; }
    public void setVersion(String version) { this.version = version; }

    public String getDescription() { return description; }
    public void setDescription(String description) { this.description = description; }

    public String getFramework() { return framework; }
    public void setFramework(String framework) { this.framework = framework; }
}
