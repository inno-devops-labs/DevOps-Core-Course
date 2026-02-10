package main

import (
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"
	"time"
)

// --- GET / endpoint tests ---

func TestMainHandler_StatusCode(t *testing.T) {
	req := httptest.NewRequest("GET", "/", nil)
	w := httptest.NewRecorder()
	mainHandler(w, req)

	if w.Code != http.StatusOK {
		t.Errorf("expected status 200, got %d", w.Code)
	}
}

func TestMainHandler_ContentType(t *testing.T) {
	req := httptest.NewRequest("GET", "/", nil)
	w := httptest.NewRecorder()
	mainHandler(w, req)

	ct := w.Header().Get("Content-Type")
	if ct != "application/json" {
		t.Errorf("expected application/json, got %s", ct)
	}
}

func TestMainHandler_ServiceFields(t *testing.T) {
	req := httptest.NewRequest("GET", "/", nil)
	w := httptest.NewRecorder()
	mainHandler(w, req)

	var data ServiceInfo
	if err := json.NewDecoder(w.Body).Decode(&data); err != nil {
		t.Fatalf("failed to decode JSON: %v", err)
	}

	if data.Service.Name != "devops-info-service" {
		t.Errorf("expected service name 'devops-info-service', got %s", data.Service.Name)
	}
	if data.Service.Version != "1.0.0" {
		t.Errorf("expected version '1.0.0', got %s", data.Service.Version)
	}
	if data.Service.Framework != "Go net/http" {
		t.Errorf("expected framework 'Go net/http', got %s", data.Service.Framework)
	}
}

func TestMainHandler_SystemFields(t *testing.T) {
	req := httptest.NewRequest("GET", "/", nil)
	w := httptest.NewRecorder()
	mainHandler(w, req)

	var data ServiceInfo
	if err := json.NewDecoder(w.Body).Decode(&data); err != nil {
		t.Fatalf("failed to decode JSON: %v", err)
	}

	if data.System.Hostname == "" {
		t.Error("hostname should not be empty")
	}
	if data.System.Platform == "" {
		t.Error("platform should not be empty")
	}
	if data.System.CPUCount <= 0 {
		t.Errorf("cpu_count should be positive, got %d", data.System.CPUCount)
	}
	if data.System.GoVersion == "" {
		t.Error("go_version should not be empty")
	}
}

func TestMainHandler_RuntimeFields(t *testing.T) {
	req := httptest.NewRequest("GET", "/", nil)
	w := httptest.NewRecorder()
	mainHandler(w, req)

	var data ServiceInfo
	if err := json.NewDecoder(w.Body).Decode(&data); err != nil {
		t.Fatalf("failed to decode JSON: %v", err)
	}

	if data.Runtime.UptimeSeconds < 0 {
		t.Errorf("uptime should be non-negative, got %d", data.Runtime.UptimeSeconds)
	}
	if data.Runtime.Timezone != "UTC" {
		t.Errorf("expected timezone 'UTC', got %s", data.Runtime.Timezone)
	}
	if data.Runtime.CurrentTime == "" {
		t.Error("current_time should not be empty")
	}
}

func TestMainHandler_RequestFields(t *testing.T) {
	req := httptest.NewRequest("GET", "/", nil)
	req.Header.Set("User-Agent", "TestBot/1.0")
	w := httptest.NewRecorder()
	mainHandler(w, req)

	var data ServiceInfo
	if err := json.NewDecoder(w.Body).Decode(&data); err != nil {
		t.Fatalf("failed to decode JSON: %v", err)
	}

	if data.Request.Method != "GET" {
		t.Errorf("expected method 'GET', got %s", data.Request.Method)
	}
	if data.Request.Path != "/" {
		t.Errorf("expected path '/', got %s", data.Request.Path)
	}
	if data.Request.UserAgent != "TestBot/1.0" {
		t.Errorf("expected user agent 'TestBot/1.0', got %s", data.Request.UserAgent)
	}
}

func TestMainHandler_Endpoints(t *testing.T) {
	req := httptest.NewRequest("GET", "/", nil)
	w := httptest.NewRecorder()
	mainHandler(w, req)

	var data ServiceInfo
	if err := json.NewDecoder(w.Body).Decode(&data); err != nil {
		t.Fatalf("failed to decode JSON: %v", err)
	}

	if len(data.Endpoints) != 2 {
		t.Fatalf("expected 2 endpoints, got %d", len(data.Endpoints))
	}

	paths := map[string]bool{}
	for _, ep := range data.Endpoints {
		paths[ep.Path] = true
	}
	if !paths["/"] {
		t.Error("missing / endpoint")
	}
	if !paths["/health"] {
		t.Error("missing /health endpoint")
	}
}

// --- GET /health endpoint tests ---

func TestHealthHandler_StatusCode(t *testing.T) {
	req := httptest.NewRequest("GET", "/health", nil)
	w := httptest.NewRecorder()
	healthHandler(w, req)

	if w.Code != http.StatusOK {
		t.Errorf("expected status 200, got %d", w.Code)
	}
}

func TestHealthHandler_ContentType(t *testing.T) {
	req := httptest.NewRequest("GET", "/health", nil)
	w := httptest.NewRecorder()
	healthHandler(w, req)

	ct := w.Header().Get("Content-Type")
	if ct != "application/json" {
		t.Errorf("expected application/json, got %s", ct)
	}
}

func TestHealthHandler_Fields(t *testing.T) {
	req := httptest.NewRequest("GET", "/health", nil)
	w := httptest.NewRecorder()
	healthHandler(w, req)

	var data HealthResponse
	if err := json.NewDecoder(w.Body).Decode(&data); err != nil {
		t.Fatalf("failed to decode JSON: %v", err)
	}

	if data.Status != "healthy" {
		t.Errorf("expected status 'healthy', got %s", data.Status)
	}
	if data.Timestamp == "" {
		t.Error("timestamp should not be empty")
	}
	if data.UptimeSeconds < 0 {
		t.Errorf("uptime should be non-negative, got %d", data.UptimeSeconds)
	}
}

// --- Error handling tests ---

func TestNotFoundHandler(t *testing.T) {
	req := httptest.NewRequest("GET", "/nonexistent", nil)
	w := httptest.NewRecorder()
	notFoundHandler(w, req)

	if w.Code != http.StatusNotFound {
		t.Errorf("expected status 404, got %d", w.Code)
	}

	var data map[string]string
	if err := json.NewDecoder(w.Body).Decode(&data); err != nil {
		t.Fatalf("failed to decode JSON: %v", err)
	}

	if data["error"] != "Not Found" {
		t.Errorf("expected error 'Not Found', got %s", data["error"])
	}
}

func TestMainHandler_NotFoundForWrongPath(t *testing.T) {
	req := httptest.NewRequest("GET", "/wrong", nil)
	w := httptest.NewRecorder()
	mainHandler(w, req)

	if w.Code != http.StatusNotFound {
		t.Errorf("expected status 404, got %d", w.Code)
	}
}

// --- Helper function tests ---

func TestGetHostname(t *testing.T) {
	hostname := getHostname()
	if hostname == "" {
		t.Error("hostname should not be empty")
	}
}

func TestGetUptime(t *testing.T) {
	seconds, human := getUptime()
	if seconds < 0 {
		t.Errorf("uptime should be non-negative, got %d", seconds)
	}
	if human == "" {
		t.Error("human uptime should not be empty")
	}
}

func TestGetClientIP(t *testing.T) {
	req := httptest.NewRequest("GET", "/", nil)
	ip := getClientIP(req)
	if ip == "" {
		t.Error("client IP should not be empty")
	}
}

func TestGetClientIP_XRealIP(t *testing.T) {
	req := httptest.NewRequest("GET", "/", nil)
	req.Header.Set("X-Real-IP", "10.0.0.1")
	ip := getClientIP(req)
	if ip != "10.0.0.1" {
		t.Errorf("expected '10.0.0.1', got %s", ip)
	}
}

func TestGetClientIP_XForwardedFor(t *testing.T) {
	req := httptest.NewRequest("GET", "/", nil)
	req.Header.Set("X-Forwarded-For", "10.0.0.2")
	ip := getClientIP(req)
	if ip != "10.0.0.2" {
		t.Errorf("expected '10.0.0.2', got %s", ip)
	}
}

func TestGetUptime_WithHours(t *testing.T) {
	// Save original startTime and restore after test
	original := startTime
	defer func() { startTime = original }()

	// Set startTime to 2 hours and 5 minutes ago
	startTime = time.Now().Add(-2*time.Hour - 5*time.Minute)

	seconds, human := getUptime()
	if seconds < 7200 {
		t.Errorf("expected at least 7200 seconds, got %d", seconds)
	}
	if human == "" {
		t.Error("human uptime should not be empty")
	}
	// Should contain "hour" when uptime > 1 hour
	if !contains(human, "hour") {
		t.Errorf("expected 'hour' in human string, got %s", human)
	}
}

func TestGetUptime_ExactlyOneHourOneMinute(t *testing.T) {
	original := startTime
	defer func() { startTime = original }()

	// Exactly 1 hour 1 minute — tests singular "hour" and "minute"
	startTime = time.Now().Add(-1*time.Hour - 1*time.Minute)

	_, human := getUptime()
	if !contains(human, "hour,") {
		t.Errorf("expected singular 'hour' in string, got %s", human)
	}
}

func TestGetUptime_ExactlyOneMinute(t *testing.T) {
	original := startTime
	defer func() { startTime = original }()

	// Exactly 1 minute — tests singular "minute" in else branch
	startTime = time.Now().Add(-1 * time.Minute)

	_, human := getUptime()
	if !contains(human, "minute") {
		t.Errorf("expected 'minute' in string, got %s", human)
	}
}

// helper
func contains(s, substr string) bool {
	return len(s) >= len(substr) && searchString(s, substr)
}

func searchString(s, substr string) bool {
	for i := 0; i <= len(s)-len(substr); i++ {
		if s[i:i+len(substr)] == substr {
			return true
		}
	}
	return false
}
