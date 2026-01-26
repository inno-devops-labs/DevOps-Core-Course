package com.example.app_java.dto;

public class ErrorResponse {
    private String error;
    private String message;
    private String timestamp;
    public ErrorResponse(String error, String message, String timestamp) {
        this.error = error;
        this.message = message;
        this.timestamp = timestamp;
    }
    public ErrorResponse() {
        //TODO Auto-generated constructor stub
    }
    public String getError() {
        return error;
    }
    public String getMessage() {
        return message;
    }
    public String getTimestamp() {
        return timestamp;
    }
    public void setError(String error) {
        this.error = error;
    }
    public void setMessage(String message) {
        this.message = message;
    }
    public void setTimestamp(String timestamp) {
        this.timestamp = timestamp;
    }
}
