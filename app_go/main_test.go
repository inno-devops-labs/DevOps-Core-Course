package main

import (
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"
	"time"
)

// TestMainHandler tests the main endpoint handler
func TestMainHandler(t *testing.T) {
	// Create a request to the main endpoint
	req, err := http.NewRequest("GET", "/", nil)
	if err != nil {
		t.Fatal(err)
	}

	// Create a ResponseRecorder to record the response
	rr := httptest.NewRecorder()
	handler := http.HandlerFunc(mainHandler)

	// Call the handler
	handler.ServeHTTP(rr, req)

	// Check the status code
	if status := rr.Code; status != http.StatusOK {
		t.Errorf("handler returned wrong status code: got %v want %v", status, http.StatusOK)
	}

	// Check the content type
	if contentType := rr.Header().Get("Content-Type"); contentType != "application/json" {
		t.Errorf("handler returned wrong content type: got %v want %v", contentType, "application/json")
	}

	// Parse and check the response body
	var info ServiceInfo
	if err := json.NewDecoder(rr.Body).Decode(&info); err != nil {
		t.Fatalf("Failed to decode JSON response: %v", err)
	}

	// Validate service information
	if info.Service.Name != "devops-info-service" {
		t.Errorf("Expected service name 'devops-info-service', got '%s'", info.Service.Name)
	}
	if info.Service.Version != "1.0.0" {
		t.Errorf("Expected version '1.0.0', got '%s'", info.Service.Version)
	}
	if info.Service.Framework != "Go net/http" {
		t.Errorf("Expected framework 'Go net/http', got '%s'", info.Service.Framework)
	}

	// Validate system information
	if info.System.Hostname == "" {
		t.Error("Hostname should not be empty")
	}
	if info.System.Platform == "" {
		t.Error("Platform should not be empty")
	}
	if info.System.Architecture == "" {
		t.Error("Architecture should not be empty")
	}
	if info.System.CPUCount <= 0 {
		t.Errorf("CPU count should be greater than 0, got %d", info.System.CPUCount)
	}
	if info.System.GoVersion == "" {
		t.Error("Go version should not be empty")
	}

	// Validate runtime information
	if info.Runtime.UptimeSeconds < 0 {
		t.Errorf("Uptime seconds should be non-negative, got %d", info.Runtime.UptimeSeconds)
	}
	if info.Runtime.UptimeHuman == "" {
		t.Error("Uptime human should not be empty")
	}
	if info.Runtime.Timezone != "UTC" {
		t.Errorf("Expected timezone 'UTC', got '%s'", info.Runtime.Timezone)
	}

	// Validate timestamp format
	if _, err := time.Parse(time.RFC3339, info.Runtime.CurrentTime); err != nil {
		t.Errorf("Invalid timestamp format: %v", err)
	}

	// Validate request information
	if info.Request.Method != "GET" {
		t.Errorf("Expected method 'GET', got '%s'", info.Request.Method)
	}
	if info.Request.Path != "/" {
		t.Errorf("Expected path '/', got '%s'", info.Request.Path)
	}

	// Validate endpoints list
	if len(info.Endpoints) < 2 {
		t.Errorf("Expected at least 2 endpoints, got %d", len(info.Endpoints))
	}
}

// TestHealthHandler tests the health check endpoint handler
func TestHealthHandler(t *testing.T) {
	// Create a request to the health endpoint
	req, err := http.NewRequest("GET", "/health", nil)
	if err != nil {
		t.Fatal(err)
	}

	// Create a ResponseRecorder
	rr := httptest.NewRecorder()
	handler := http.HandlerFunc(healthHandler)

	// Call the handler
	handler.ServeHTTP(rr, req)

	// Check the status code
	if status := rr.Code; status != http.StatusOK {
		t.Errorf("handler returned wrong status code: got %v want %v", status, http.StatusOK)
	}

	// Check the content type
	if contentType := rr.Header().Get("Content-Type"); contentType != "application/json" {
		t.Errorf("handler returned wrong content type: got %v want %v", contentType, "application/json")
	}

	// Parse and check the response body
	var health HealthResponse
	if err := json.NewDecoder(rr.Body).Decode(&health); err != nil {
		t.Fatalf("Failed to decode JSON response: %v", err)
	}

	// Validate health status
	if health.Status != "healthy" {
		t.Errorf("Expected status 'healthy', got '%s'", health.Status)
	}

	// Validate uptime
	if health.UptimeSeconds < 0 {
		t.Errorf("Uptime seconds should be non-negative, got %d", health.UptimeSeconds)
	}

	// Validate timestamp format
	if _, err := time.Parse(time.RFC3339, health.Timestamp); err != nil {
		t.Errorf("Invalid timestamp format: %v", err)
	}
}

// TestErrorHandler tests the 404 error handler
func TestErrorHandler(t *testing.T) {
	// Create a request to a non-existent endpoint
	req, err := http.NewRequest("GET", "/nonexistent", nil)
	if err != nil {
		t.Fatal(err)
	}

	// Create a ResponseRecorder
	rr := httptest.NewRecorder()
	handler := http.HandlerFunc(errorHandler)

	// Call the handler
	handler.ServeHTTP(rr, req)

	// Check the status code
	if status := rr.Code; status != http.StatusNotFound {
		t.Errorf("handler returned wrong status code: got %v want %v", status, http.StatusNotFound)
	}

	// Check the content type
	if contentType := rr.Header().Get("Content-Type"); contentType != "application/json" {
		t.Errorf("handler returned wrong content type: got %v want %v", contentType, "application/json")
	}

	// Parse and check the response body
	var errorResp ErrorResponse
	if err := json.NewDecoder(rr.Body).Decode(&errorResp); err != nil {
		t.Fatalf("Failed to decode JSON response: %v", err)
	}

	// Validate error response
	if errorResp.Error != "Not Found" {
		t.Errorf("Expected error 'Not Found', got '%s'", errorResp.Error)
	}
	if errorResp.Message == "" {
		t.Error("Error message should not be empty")
	}
}

// TestGetUptime tests the uptime calculation function
func TestGetUptime(t *testing.T) {
	uptime := getUptime()

	if uptime.UptimeSeconds < 0 {
		t.Errorf("Uptime seconds should be non-negative, got %d", uptime.UptimeSeconds)
	}

	if uptime.UptimeHuman == "" {
		t.Error("Uptime human should not be empty")
	}

	if uptime.Timezone != "UTC" {
		t.Errorf("Expected timezone 'UTC', got '%s'", uptime.Timezone)
	}

	// Validate timestamp format
	if _, err := time.Parse(time.RFC3339, uptime.CurrentTime); err != nil {
		t.Errorf("Invalid timestamp format: %v", err)
	}
}

// TestGetSystemInfo tests the system info collection function
func TestGetSystemInfo(t *testing.T) {
	system := getSystemInfo()

	if system.Hostname == "" {
		t.Error("Hostname should not be empty")
	}

	if system.Platform == "" {
		t.Error("Platform should not be empty")
	}

	if system.Architecture == "" {
		t.Error("Architecture should not be empty")
	}

	if system.CPUCount <= 0 {
		t.Errorf("CPU count should be greater than 0, got %d", system.CPUCount)
	}

	if system.GoVersion == "" {
		t.Error("Go version should not be empty")
	}
}

// TestPlural tests the plural helper function
func TestPlural(t *testing.T) {
	tests := []struct {
		name     string
		input    int
		expected string
	}{
		{"Singular", 1, ""},
		{"Plural", 0, "s"},
		{"Plural two", 2, "s"},
		{"Plural many", 10, "s"},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := plural(tt.input)
			if result != tt.expected {
				t.Errorf("plural(%d) = %s; want %s", tt.input, result, tt.expected)
			}
		})
	}
}

// TestGetRequestInfo tests the request info collection function
func TestGetRequestInfo(t *testing.T) {
	// Create a test request
	req, err := http.NewRequest("GET", "/test", nil)
	if err != nil {
		t.Fatal(err)
	}
	req.Header.Set("User-Agent", "test-agent")
	req.RemoteAddr = "192.168.1.1:12345" // Set a remote address for testing

	requestInfo := getRequestInfo(req)

	if requestInfo.Method != "GET" {
		t.Errorf("Expected method 'GET', got '%s'", requestInfo.Method)
	}

	if requestInfo.Path != "/test" {
		t.Errorf("Expected path '/test', got '%s'", requestInfo.Path)
	}

	if requestInfo.UserAgent != "test-agent" {
		t.Errorf("Expected User-Agent 'test-agent', got '%s'", requestInfo.UserAgent)
	}

	if requestInfo.ClientIP == "" {
		t.Error("Client IP should not be empty")
	}

	if requestInfo.ClientIP != "192.168.1.1" {
		t.Errorf("Expected client IP '192.168.1.1', got '%s'", requestInfo.ClientIP)
	}
}

// TestMainHandlerWithDifferentMethods tests main handler with different HTTP methods
func TestMainHandlerWithDifferentMethods(t *testing.T) {
	methods := []string{"GET", "POST", "PUT", "DELETE"}

	for _, method := range methods {
		t.Run(method, func(t *testing.T) {
			req, err := http.NewRequest(method, "/", nil)
			if err != nil {
				t.Fatal(err)
			}

			rr := httptest.NewRecorder()
			handler := http.HandlerFunc(mainHandler)
			handler.ServeHTTP(rr, req)

			if status := rr.Code; status != http.StatusOK {
				t.Errorf("%s: handler returned wrong status code: got %v want %v", method, status, http.StatusOK)
			}

			var info ServiceInfo
			if err := json.NewDecoder(rr.Body).Decode(&info); err != nil {
				t.Fatalf("Failed to decode JSON response: %v", err)
			}

			if info.Request.Method != method {
				t.Errorf("Expected method '%s', got '%s'", method, info.Request.Method)
			}
		})
	}
}

// TestUptimeIncrements tests that uptime increases over time
func TestUptimeIncrements(t *testing.T) {
	uptime1 := getUptime()
	time.Sleep(100 * time.Millisecond)
	uptime2 := getUptime()

	if uptime2.UptimeSeconds < uptime1.UptimeSeconds {
		t.Error("Uptime should not decrease")
	}
}
