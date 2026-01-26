package com.example.app_java.dto;

public class ServiceInfo {
    public ServiceInfo(String name, String version, String description, String framework) {
        this.name = name;
        this.version = version;
        this.description = description;
        this.framework = framework;
    }
    
    public ServiceInfo() {
        //TODO Auto-generated constructor stub
    }

    private String name;
    private String version;
    private String description;
    private String framework;
    
    public String getName() {
        return name;
    }
    public String getVersion() {
        return version;
    }
    public String getDescription() {
        return description;
    }
    public String getFramework() {
        return framework;
    }
    public void setName(String name) {
        this.name = name;
    }
    public void setVersion(String version) {
        this.version = version;
    }
    public void setDescription(String description) {
        this.description = description;
    }
    public void setFramework(String framework) {
        this.framework = framework;
    }
}
