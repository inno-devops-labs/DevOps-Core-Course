package main

import (
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"
)

// TestMainHandler_StatusCode checks that GET / returns 200.
func TestMainHandler_StatusCode(t *testing.T) {
	req := httptest.NewRequest(http.MethodGet, "/", nil)
	w := httptest.NewRecorder()

	mainHandler(w, req)

	if w.Code != http.StatusOK {
		t.Errorf("expected status 200, got %d", w.Code)
	}
}

// TestMainHandler_JSON checks that the response is valid JSON with required top-level keys.
func TestMainHandler_JSON(t *testing.T) {
	req := httptest.NewRequest(http.MethodGet, "/", nil)
	w := httptest.NewRecorder()

	mainHandler(w, req)

	var result map[string]interface{}
	if err := json.Unmarshal(w.Body.Bytes(), &result); err != nil {
		t.Fatalf("response is not valid JSON: %v", err)
	}

	for _, key := range []string{"service", "system", "runtime", "request", "endpoints"} {
		if _, ok := result[key]; !ok {
			t.Errorf("missing top-level key %q", key)
		}
	}
}

// TestMainHandler_ServiceFields checks service section fields.
func TestMainHandler_ServiceFields(t *testing.T) {
	req := httptest.NewRequest(http.MethodGet, "/", nil)
	w := httptest.NewRecorder()

	mainHandler(w, req)

	var result ServiceInfo
	if err := json.Unmarshal(w.Body.Bytes(), &result); err != nil {
		t.Fatalf("failed to decode response: %v", err)
	}

	if result.Service.Name != "devops-info-service" {
		t.Errorf("unexpected service name: %s", result.Service.Name)
	}
	if result.Service.Version != "1.0.0" {
		t.Errorf("unexpected service version: %s", result.Service.Version)
	}
	if result.Service.Framework != "Go net/http" {
		t.Errorf("unexpected framework: %s", result.Service.Framework)
	}
}

// TestHealthHandler_StatusCode checks that GET /health returns 200.
func TestHealthHandler_StatusCode(t *testing.T) {
	req := httptest.NewRequest(http.MethodGet, "/health", nil)
	w := httptest.NewRecorder()

	healthHandler(w, req)

	if w.Code != http.StatusOK {
		t.Errorf("expected status 200, got %d", w.Code)
	}
}

// TestHealthHandler_JSON checks the health response fields.
func TestHealthHandler_JSON(t *testing.T) {
	req := httptest.NewRequest(http.MethodGet, "/health", nil)
	w := httptest.NewRecorder()

	healthHandler(w, req)

	var result HealthResponse
	if err := json.Unmarshal(w.Body.Bytes(), &result); err != nil {
		t.Fatalf("failed to decode health response: %v", err)
	}

	if result.Status != "healthy" {
		t.Errorf("expected status 'healthy', got %q", result.Status)
	}
	if result.UptimeSeconds < 0 {
		t.Errorf("uptime should be non-negative, got %d", result.UptimeSeconds)
	}
	if result.Timestamp == "" {
		t.Error("timestamp should not be empty")
	}
}

// TestNotFound checks that unknown paths return 404.
func TestNotFound(t *testing.T) {
	req := httptest.NewRequest(http.MethodGet, "/nonexistent", nil)
	w := httptest.NewRecorder()

	mainHandler(w, req)

	if w.Code != http.StatusNotFound {
		t.Errorf("expected status 404, got %d", w.Code)
	}

	var result ErrorResponse
	if err := json.Unmarshal(w.Body.Bytes(), &result); err != nil {
		t.Fatalf("failed to decode error response: %v", err)
	}
	if result.Error != "Not Found" {
		t.Errorf("unexpected error field: %q", result.Error)
	}
}

// TestGetUptime checks the getUptime helper.
func TestGetUptime(t *testing.T) {
	seconds, human := getUptime()
	if seconds < 0 {
		t.Error("uptime seconds should be non-negative")
	}
	if human == "" {
		t.Error("human-readable uptime should not be empty")
	}
}

// TestGetHostname checks that hostname is not empty.
func TestGetHostname(t *testing.T) {
	h := getHostname()
	if h == "" {
		t.Error("hostname should not be empty")
	}
}

// TestContentType checks that handlers return application/json.
func TestContentType(t *testing.T) {
	tests := []struct {
		name    string
		path    string
		handler http.HandlerFunc
	}{
		{"main", "/", mainHandler},
		{"health", "/health", healthHandler},
	}

	for _, tc := range tests {
		t.Run(tc.name, func(t *testing.T) {
			req := httptest.NewRequest(http.MethodGet, tc.path, nil)
			w := httptest.NewRecorder()
			tc.handler(w, req)

			ct := w.Header().Get("Content-Type")
			if ct != "application/json" {
				t.Errorf("expected Content-Type application/json, got %q", ct)
			}
		})
	}
}
