package com.example.app_java.dto;

public class HealthResponse {
    private String status;
    private String timestamp;
    private Long uptimeSeconds;
    public HealthResponse(String status, String timestamp, Long uptimeSeconds) {
        this.status = status;
        this.timestamp = timestamp;
        this.uptimeSeconds = uptimeSeconds;
    }
    public HealthResponse() {
        //TODO Auto-generated constructor stub
    }
    public String getStatus() {
        return status;
    }
    public String getTimestamp() {
        return timestamp;
    }
    public Long getUptimeSeconds() {
        return uptimeSeconds;
    }
    public void setStatus(String status) {
        this.status = status;
    }
    public void setTimestamp(String timestamp) {
        this.timestamp = timestamp;
    }
    public void setUptimeSeconds(Long uptimeSeconds) {
        this.uptimeSeconds = uptimeSeconds;
    }
}
