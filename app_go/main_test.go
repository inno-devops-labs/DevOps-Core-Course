package main

import (
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"
	"time"
)

// TestMainEndpoint tests the main endpoint
func TestMainEndpoint(t *testing.T) {
	req, err := http.NewRequest("GET", "/", nil)
	if err != nil {
		t.Fatal(err)
	}

	rr := httptest.NewRecorder()
	handler := http.HandlerFunc(mainHandler)

	handler.ServeHTTP(rr, req)

	// Check status code
	if status := rr.Code; status != http.StatusOK {
		t.Errorf("handler returned wrong status code: got %v want %v",
			status, http.StatusOK)
	}

	// Check content type
	contentType := rr.Header().Get("Content-Type")
	if contentType != "application/json" {
		t.Errorf("handler returned wrong content type: got %v want %v",
			contentType, "application/json")
	}

	// Parse JSON response
	var response map[string]interface{}
	if err := json.Unmarshal(rr.Body.Bytes(), &response); err != nil {
		t.Errorf("Failed to parse JSON response: %v", err)
	}

	// Check required top-level fields
	requiredFields := []string{"service", "system", "runtime", "request", "endpoints"}
	for _, field := range requiredFields {
		if _, ok := response[field]; !ok {
			t.Errorf("Response missing required field: %s", field)
		}
	}

	// Check service section
	service, ok := response["service"].(map[string]interface{})
	if !ok {
		t.Error("Service field is not a map")
	} else {
		if service["name"] != "devops-info-service" {
			t.Errorf("Service name incorrect: got %v", service["name"])
		}
		if service["framework"] != "Go net/http" {
			t.Errorf("Service framework incorrect: got %v", service["framework"])
		}
	}
}

// TestHealthEndpoint tests the health check endpoint
func TestHealthEndpoint(t *testing.T) {
	req, err := http.NewRequest("GET", "/health", nil)
	if err != nil {
		t.Fatal(err)
	}

	rr := httptest.NewRecorder()
	handler := http.HandlerFunc(healthHandler)

	handler.ServeHTTP(rr, req)

	// Check status code
	if status := rr.Code; status != http.StatusOK {
		t.Errorf("handler returned wrong status code: got %v want %v",
			status, http.StatusOK)
	}

	// Check content type
	contentType := rr.Header().Get("Content-Type")
	if contentType != "application/json" {
		t.Errorf("handler returned wrong content type: got %v want %v",
			contentType, "application/json")
	}

	// Parse JSON response
	var response map[string]interface{}
	if err := json.Unmarshal(rr.Body.Bytes(), &response); err != nil {
		t.Errorf("Failed to parse JSON response: %v", err)
	}

	// Check required fields
	requiredFields := []string{"status", "timestamp", "uptime_seconds"}
	for _, field := range requiredFields {
		if _, ok := response[field]; !ok {
			t.Errorf("Health response missing required field: %s", field)
		}
	}

	// Check status value
	if response["status"] != "healthy" {
		t.Errorf("Health status incorrect: got %v want %v",
			response["status"], "healthy")
	}

	// Check uptime is a number
	if _, ok := response["uptime_seconds"].(float64); !ok {
		t.Errorf("uptime_seconds is not a number: %v", response["uptime_seconds"])
	}
}

// TestGetSystemInfo tests the system info collection
func TestGetSystemInfo(t *testing.T) {
	info := getSystemInfo()

	if info.Hostname == "" {
		t.Error("Hostname should not be empty")
	}

	if info.Platform == "" {
		t.Error("Platform should not be empty")
	}

	if info.CPUCount <= 0 {
		t.Errorf("CPU count should be positive: got %d", info.CPUCount)
	}

	if info.GoVersion == "" {
		t.Error("Go version should not be empty")
	}
}

// TestGetUptime tests the uptime calculation
func TestGetUptime(t *testing.T) {
	// Wait a bit to ensure uptime is non-zero
	time.Sleep(100 * time.Millisecond)

	seconds, human := getUptime()

	if seconds < 0 {
		t.Errorf("Uptime should be non-negative: got %d", seconds)
	}

	if human == "" {
		t.Error("Human-readable uptime should not be empty")
	}
}

// TestNotFoundHandler tests 404 error handling
func TestNotFoundHandler(t *testing.T) {
	req, err := http.NewRequest("GET", "/nonexistent", nil)
	if err != nil {
		t.Fatal(err)
	}

	rr := httptest.NewRecorder()
	handler := http.HandlerFunc(notFoundHandler)

	handler.ServeHTTP(rr, req)

	// Check status code
	if status := rr.Code; status != http.StatusNotFound {
		t.Errorf("handler returned wrong status code: got %v want %v",
			status, http.StatusNotFound)
	}

	// Parse JSON response
	var response map[string]interface{}
	if err := json.Unmarshal(rr.Body.Bytes(), &response); err != nil {
		t.Errorf("Failed to parse JSON response: %v", err)
	}

	// Check error field
	if response["error"] != "Not Found" {
		t.Errorf("Error message incorrect: got %v", response["error"])
	}
}

// TestConcurrentRequests tests that the service handles concurrent requests
func TestConcurrentRequests(t *testing.T) {
	const numRequests = 10
	done := make(chan bool, numRequests)

	for i := 0; i < numRequests; i++ {
		go func() {
			req, _ := http.NewRequest("GET", "/", nil)
			rr := httptest.NewRecorder()
			handler := http.HandlerFunc(mainHandler)
			handler.ServeHTTP(rr, req)

			if rr.Code != http.StatusOK {
				t.Errorf("Expected status 200, got %d", rr.Code)
			}
			done <- true
		}()
	}

	// Wait for all requests to complete
	for i := 0; i < numRequests; i++ {
		<-done
	}
}

// TestUptimeIncreases tests that uptime increases over time
func TestUptimeIncreases(t *testing.T) {
	seconds1, _ := getUptime()
	time.Sleep(1 * time.Second)
	seconds2, _ := getUptime()

	if seconds2 <= seconds1 {
		t.Errorf("Uptime should increase: got %d then %d", seconds1, seconds2)
	}
}
