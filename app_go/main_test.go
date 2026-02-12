package main

import (
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"
)

func TestRootHandler(t *testing.T) {
	req := httptest.NewRequest("GET", "/", nil)
	w := httptest.NewRecorder()
	rootHandler(w, req)

	if w.Code != http.StatusOK {
		t.Errorf("expected 200, got %d", w.Code)
	}

	var resp RootResponse
	if err := json.Unmarshal(w.Body.Bytes(), &resp); err != nil {
		t.Fatalf("failed to parse JSON: %v", err)
	}

	if resp.Service.Name != "devops-info-service" {
		t.Errorf("expected service name 'devops-info-service', got '%s'", resp.Service.Name)
	}
	if resp.Service.Version != "1.0.0" {
		t.Errorf("expected version '1.0.0', got '%s'", resp.Service.Version)
	}
	if resp.Service.Framework != "net/http" {
		t.Errorf("expected framework 'net/http', got '%s'", resp.Service.Framework)
	}
	if resp.System.CPUCount <= 0 {
		t.Errorf("expected cpu_count > 0, got %d", resp.System.CPUCount)
	}
	if resp.Runtime.Timezone != "UTC" {
		t.Errorf("expected timezone 'UTC', got '%s'", resp.Runtime.Timezone)
	}
	if len(resp.Endpoints) < 2 {
		t.Errorf("expected at least 2 endpoints, got %d", len(resp.Endpoints))
	}
}

func TestHealthHandler(t *testing.T) {
	req := httptest.NewRequest("GET", "/health", nil)
	w := httptest.NewRecorder()
	healthHandler(w, req)

	if w.Code != http.StatusOK {
		t.Errorf("expected 200, got %d", w.Code)
	}

	var resp HealthResponse
	if err := json.Unmarshal(w.Body.Bytes(), &resp); err != nil {
		t.Fatalf("failed to parse JSON: %v", err)
	}

	if resp.Status != "healthy" {
		t.Errorf("expected status 'healthy', got '%s'", resp.Status)
	}
	if resp.UptimeSeconds < 0 {
		t.Errorf("expected uptime >= 0, got %d", resp.UptimeSeconds)
	}
	if resp.Timestamp == "" {
		t.Error("expected non-empty timestamp")
	}
}

func TestRootHandlerNotFound(t *testing.T) {
	req := httptest.NewRequest("GET", "/nonexistent", nil)
	w := httptest.NewRecorder()
	rootHandler(w, req)

	if w.Code != http.StatusNotFound {
		t.Errorf("expected 404, got %d", w.Code)
	}
}

func TestRootHandlerContentType(t *testing.T) {
	req := httptest.NewRequest("GET", "/", nil)
	w := httptest.NewRecorder()
	rootHandler(w, req)

	ct := w.Header().Get("Content-Type")
	if ct != "application/json" {
		t.Errorf("expected content-type 'application/json', got '%s'", ct)
	}
}
