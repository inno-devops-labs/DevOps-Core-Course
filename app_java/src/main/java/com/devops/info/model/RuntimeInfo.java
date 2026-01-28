package com.devops.info.model;

public class RuntimeInfo {
    private long uptimeSeconds;
    private String uptimeHuman;
    private String currentTime;
    private String timezone;

    // Getters and Setters
    public long getUptimeSeconds() { return uptimeSeconds; }
    public void setUptimeSeconds(long uptimeSeconds) { this.uptimeSeconds = uptimeSeconds; }

    public String getUptimeHuman() { return uptimeHuman; }
    public void setUptimeHuman(String uptimeHuman) { this.uptimeHuman = uptimeHuman; }

    public String getCurrentTime() { return currentTime; }
    public void setCurrentTime(String currentTime) { this.currentTime = currentTime; }

    public String getTimezone() { return timezone; }
    public void setTimezone(String timezone) { this.timezone = timezone; }
}
