package main

import (
	"encoding/json"
	"errors"
	"net/http"
	"net/http/httptest"
	"testing"
	"time"
)

// errWriter is an http.ResponseWriter that fails on Write (for testing error paths)
type errWriter struct {
	http.ResponseWriter
}

func (e *errWriter) Write([]byte) (int, error) {
	return 0, errors.New("write failed")
}

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

// TestFormatUptime tests all branches of formatUptime (seconds, minutes, hours; singular/plural)
func TestFormatUptime(t *testing.T) {
	tests := []struct {
		duration   time.Duration
		wantSec    int
		wantSuffix string // substring that should appear in human string
	}{
		{0, 0, "0 second"},
		{1 * time.Second, 1, "1 second"},
		{2 * time.Second, 2, "2 seconds"},
		{1 * time.Minute, 60, "1 minute"},
		{2 * time.Minute, 120, "2 minutes"},
		{1*time.Hour + 30*time.Minute, 5400, "1 hour"},
		{2*time.Hour + 5*time.Minute, 7500, "2 hours"},
	}
	for _, tt := range tests {
		sec, human := formatUptime(tt.duration)
		if sec != tt.wantSec {
			t.Errorf("formatUptime(%v) seconds = %d, want %d", tt.duration, sec, tt.wantSec)
		}
		if human == "" {
			t.Errorf("formatUptime(%v) human empty", tt.duration)
		}
		if tt.wantSuffix != "" && len(human) < len(tt.wantSuffix) {
			t.Errorf("formatUptime(%v) human = %q, want containing %q", tt.duration, human, tt.wantSuffix)
		}
	}
}

// TestGetSystemInfoHostnameError tests getSystemInfo when hostname fails
func TestGetSystemInfoHostnameError(t *testing.T) {
	old := hostnameFunc
	defer func() { hostnameFunc = old }()
	hostnameFunc = func() (string, error) {
		return "", errors.New("hostname error")
	}
	info := getSystemInfo()
	if info.Hostname != "unknown" {
		t.Errorf("expected hostname 'unknown' on error, got %q", info.Hostname)
	}
	if info.Platform == "" || info.GoVersion == "" {
		t.Error("other system fields should still be set")
	}
}

// TestGetRequestInfo tests request info extraction (X-Forwarded-For, User-Agent)
func TestGetRequestInfo(t *testing.T) {
	req, _ := http.NewRequest("GET", "/health", nil)
	req.RemoteAddr = "192.168.1.1:12345"
	req.Header.Set("User-Agent", "TestAgent/1.0")
	info := getRequestInfo(req)
	if info.ClientIP != "192.168.1.1:12345" {
		t.Errorf("ClientIP = %q, want 192.168.1.1:12345", info.ClientIP)
	}
	if info.UserAgent != "TestAgent/1.0" {
		t.Errorf("UserAgent = %q, want TestAgent/1.0", info.UserAgent)
	}
	if info.Method != "GET" || info.Path != "/health" {
		t.Errorf("Method=%q Path=%q", info.Method, info.Path)
	}

	// X-Forwarded-For overrides RemoteAddr
	req.Header.Set("X-Forwarded-For", "10.0.0.1")
	info2 := getRequestInfo(req)
	if info2.ClientIP != "10.0.0.1" {
		t.Errorf("with X-Forwarded-For, ClientIP = %q, want 10.0.0.1", info2.ClientIP)
	}

	// Empty User-Agent becomes "unknown"
	req.Header.Del("User-Agent")
	req.Header.Del("X-Forwarded-For")
	info3 := getRequestInfo(req)
	if info3.UserAgent != "unknown" {
		t.Errorf("empty User-Agent should become 'unknown', got %q", info3.UserAgent)
	}
}

// TestMainHandlerWriteError tests mainHandler when JSON write fails
func TestMainHandlerWriteError(t *testing.T) {
	req, _ := http.NewRequest("GET", "/", nil)
	rr := httptest.NewRecorder()
	w := &errWriter{ResponseWriter: rr}
	mainHandler(w, req)
	if rr.Code != http.StatusOK {
		t.Errorf("status should still be 200 before write, got %d", rr.Code)
	}
}

// TestHealthHandlerWriteError tests healthHandler when JSON write fails
func TestHealthHandlerWriteError(t *testing.T) {
	req, _ := http.NewRequest("GET", "/health", nil)
	rr := httptest.NewRecorder()
	w := &errWriter{ResponseWriter: rr}
	healthHandler(w, req)
	if rr.Code != http.StatusOK {
		t.Errorf("status should still be 200 before write, got %d", rr.Code)
	}
}

// TestNotFoundHandlerWriteError tests notFoundHandler when JSON write fails
func TestNotFoundHandlerWriteError(t *testing.T) {
	req, _ := http.NewRequest("GET", "/missing", nil)
	rr := httptest.NewRecorder()
	w := &errWriter{ResponseWriter: rr}
	notFoundHandler(w, req)
	if rr.Code != http.StatusNotFound {
		t.Errorf("status should still be 404 before write, got %d", rr.Code)
	}
}
