package com.devops.info.model;

public class SystemInfo {
    private String hostname;
    private String platform;
    private String platformVersion;
    private String architecture;
    private int cpuCount;
    private String pythonVersion;

    // Getters and Setters
    public String getHostname() { return hostname; }
    public void setHostname(String hostname) { this.hostname = hostname; }

    public String getPlatform() { return platform; }
    public void setPlatform(String platform) { this.platform = platform; }

    public String getPlatformVersion() { return platformVersion; }
    public void setPlatformVersion(String platformVersion) { this.platformVersion = platformVersion; }

    public String getArchitecture() { return architecture; }
    public void setArchitecture(String architecture) { this.architecture = architecture; }

    public int getCpuCount() { return cpuCount; }
    public void setCpuCount(int cpuCount) { this.cpuCount = cpuCount; }

    public String getPythonVersion() { return pythonVersion; }
    public void setPythonVersion(String pythonVersion) { this.pythonVersion = pythonVersion; }
}
