package com.example.app_java.dto;

public class RuntimeInfo {
    private Long uptimeSeconds;
    private String uptimeHuman;
    private String currentTime;
    private String timezone;
    
    public RuntimeInfo(Long uptimeSeconds, String uptimeHuman, String currentTime, String timezone) {
        this.uptimeSeconds = uptimeSeconds;
        this.uptimeHuman = uptimeHuman;
        this.currentTime = currentTime;
        this.timezone = timezone;
    }

    public RuntimeInfo() {
        //TODO Auto-generated constructor stub
    }

    public Long getUptimeSeconds() {
        return uptimeSeconds;
    }

    public String getUptimeHuman() {
        return uptimeHuman;
    }

    public String getCurrentTime() {
        return currentTime;
    }

    public String getTimezone() {
        return timezone;
    }

    public void setUptimeSeconds(Long uptimeSeconds) {
        this.uptimeSeconds = uptimeSeconds;
    }

    public void setUptimeHuman(String uptimeHuman) {
        this.uptimeHuman = uptimeHuman;
    }

    public void setCurrentTime(String currentTime) {
        this.currentTime = currentTime;
    }

    public void setTimezone(String timezone) {
        this.timezone = timezone;
    }
}
