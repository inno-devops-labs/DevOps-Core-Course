package com.example.app_java.dto;

public class RequestInfo {
    private String clientIp;
    private String userAgent;
    private String method;
    private String path;
    
    public RequestInfo(String clientIp, String userAgent, String method, String path) {
        this.clientIp = clientIp;
        this.userAgent = userAgent;
        this.method = method;
        this.path = path;
    }
    public RequestInfo() {
        //TODO Auto-generated constructor stub
    }
    public String getClientIp() {
        return clientIp;
    }
    public String getUserAgent() {
        return userAgent;
    }
    public String getMethod() {
        return method;
    }
    public String getPath() {
        return path;
    }
    public void setClientIp(String clientIp) {
        this.clientIp = clientIp;
    }
    public void setUserAgent(String userAgent) {
        this.userAgent = userAgent;
    }
    public void setMethod(String method) {
        this.method = method;
    }
    public void setPath(String path) {
        this.path = path;
    }
}
