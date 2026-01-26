package com.example.app_java.dto;

public class SystemInfo {
    private String hostname;
    private String platform;
    private String platformVersion;
    private String architecture;
    private Integer cpuCount;
    private String javaVersion;
    
    public SystemInfo(String hostname, String platform, String platformVersion, String architecture, Integer cpuCount,
            String javaVersion) {
        this.hostname = hostname;
        this.platform = platform;
        this.platformVersion = platformVersion;
        this.architecture = architecture;
        this.cpuCount = cpuCount;
        this.javaVersion = javaVersion;
    }

    public SystemInfo() {
        //TODO Auto-generated constructor stub
    }

    public String getHostname() {
        return hostname;
    }

    public String getPlatform() {
        return platform;
    }

    public String getPlatformVersion() {
        return platformVersion;
    }

    public String getArchitecture() {
        return architecture;
    }

    public Integer getCpuCount() {
        return cpuCount;
    }

    public String getJavaVersion() {
        return javaVersion;
    }

    public void setHostname(String hostname) {
        this.hostname = hostname;
    }

    public void setPlatform(String platform) {
        this.platform = platform;
    }

    public void setPlatformVersion(String platformVersion) {
        this.platformVersion = platformVersion;
    }

    public void setArchitecture(String architecture) {
        this.architecture = architecture;
    }

    public void setCpuCount(Integer cpuCount) {
        this.cpuCount = cpuCount;
    }

    public void setJavaVersion(String javaVersion) {
        this.javaVersion = javaVersion;
    }
}
